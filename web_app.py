#!/usr/bin/env python3
"""
News02 Web Interface
Modern dashboard for managing news digest generation
"""

import os
import json
import yaml
import asyncio
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import threading
import time
from pathlib import Path

# Import our modules
from functions.config_manager import config_manager
from functions.database import NewsDatabase
from functions.news_digest_enhanced import (
    load_feeds, fetch_articles, extract_and_summarize_articles,
    generate_broadcast_with_llm, save_digest, text_to_speech
)
from functions.news_cli import test_llm_connection, test_database

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'news02-secret-key-change-me')

# Template filters
@app.template_filter('timestamp_to_date')
def timestamp_to_date(timestamp):
    """Convert timestamp to readable date"""
    return datetime.fromtimestamp(timestamp).strftime('%B %d, %Y')

@app.template_filter('timestamp_to_time')
def timestamp_to_time(timestamp):
    """Convert timestamp to readable time"""
    return datetime.fromtimestamp(timestamp).strftime('%I:%M %p')

@app.template_filter('filesizeformat')
def filesizeformat(num_bytes):
    """Format file size in human readable format"""
    if num_bytes == 0:
        return '0 B'
    for unit in ['B', 'KB', 'MB', 'GB']:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"

# Global variables for background tasks
generation_status = {
    'running': False,
    'progress': 0,
    'stage': 'idle',
    'error': None,
    'result_file': None
}

def get_database():
    """Get database instance if enabled"""
    db_config = config_manager.get_database_config()
    return NewsDatabase(db_config['path']) if db_config['enabled'] else None

def extract_sources_from_content(content):
    """Extract source information from digest content"""
    sources = []
    lines = content.split('\n')
    
    # First, try to find the "Article Sources" section we now embed
    in_sources_section = False
    current_article = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Look for our embedded "Article Sources" section
        if line == "## Article Sources":
            in_sources_section = True
            continue
            
        if in_sources_section:
            # Pattern: "1. **Title**"
            if line and line[0].isdigit() and '**' in line:
                if current_article:
                    sources.append(current_article)
                
                # Extract title between ** markers
                import re
                title_match = re.search(r'\*\*(.*?)\*\*', line)
                if title_match:
                    title = title_match.group(1)
                    current_article = {
                        'title': title,
                        'url': None,
                        'source': None
                    }
            
            # Pattern: "   - URL: ..."
            elif current_article and line.startswith('- URL:'):
                url = line.replace('- URL:', '').strip()
                current_article['url'] = url
            
            # Pattern: "   - Source: ..."
            elif current_article and line.startswith('- Source:'):
                source = line.replace('- Source:', '').strip()
                current_article['source'] = source
    
    # Add the last article if we were in sources section
    if current_article and in_sources_section:
        sources.append(current_article)
    
    # If we found sources from the embedded section, return them
    if sources:
        return sources
    
    # Fallback: Parse older digest format or broadcast content
    current_article = None
    article_count = 0
    current_source = None
    
    for line in lines:
        line = line.strip()
        
        # Pattern 1: "From source:" headers
        if line.startswith('From ') and line.endswith(':'):
            current_source = line.replace('From ', '').replace(':', '').strip()
            continue
            
        # Pattern 2: Article bullets "- Title: Summary"
        elif line.startswith('- ') and ':' in line:
            if current_article:
                sources.append(current_article)
                
            title_part = line[2:].split(':', 1)[0].strip()
            article_count += 1
            
            current_article = {
                'title': title_part,
                'url': None,
                'source': current_source if current_source else f'Article {article_count}'
            }
            
        # Pattern 3: Headers like "### Title" or "## Title"
        elif line.startswith('###') or line.startswith('##'):
            if current_article:
                sources.append(current_article)
            
            title = line.replace('###', '').replace('##', '').strip()
            article_count += 1
            
            current_article = {
                'title': title,
                'url': None,
                'source': f'Article {article_count}'
            }
        
        # Look for URLs in the content
        elif current_article and ('http' in line or 'Source:' in line):
            import re
            url_match = re.search(r'https?://[^\s]+', line)
            if url_match:
                current_article['url'] = url_match.group()
                
                # Extract domain as source if not already set
                if not current_article['source'] or current_article['source'].startswith('Article '):
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(current_article['url']).netloc
                        current_article['source'] = domain.replace('www.', '')
                    except:
                        pass
    
    # Add the last article if exists
    if current_article:
        sources.append(current_article)
    
    # If we found actual articles, return them
    if sources and article_count > 0:
        return sources
    
    # If we have some sources from content parsing, return them
    if sources and len(sources) > 0:
        return sources
    
    # Only use database fallback if we found no sources at all from content
    try:
        db = get_database()
        if db:
            import sqlite3
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            
            # Get only very recent processed articles (last 10 minutes) to avoid mixing old digests
            cursor.execute("""
                SELECT title, link, source_feed
                FROM articles
                WHERE processed = TRUE
                AND fetched_at > datetime('now', '-10 minutes')
                ORDER BY fetched_at DESC
                LIMIT 20
            """)
            
            db_articles = cursor.fetchall()
            conn.close()
            
            for title, link, source_feed in db_articles:
                from urllib.parse import urlparse
                domain = urlparse(source_feed).netloc.replace('www.', '')
                sources.append({
                    'title': title,
                    'url': link,
                    'source': domain
                })
                
            if sources:
                return sources
    except:
        pass
    
    # Final fallback: RSS feeds
    try:
        feed_urls = load_feeds()
        for url in feed_urls:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.replace('www.', '')
            sources.append({
                'title': f'Feed: {domain}',
                'url': url,
                'source': domain
            })
    except:
        pass
    
    return sources

@app.route('/')
def dashboard():
    """Main dashboard"""
    db = get_database()
    
    # Get recent articles and analytics
    recent_articles = []
    feed_analytics = []
    recent_broadcasts = []
    
    if db:
        try:
            recent_articles = db.get_recent_articles(24)[:10]
            feed_analytics = db.get_feed_analytics()[:5]
            
            # Get recent broadcasts from database first
            import sqlite3
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM broadcasts
                ORDER BY created_at DESC
                LIMIT 5
            """)
            columns = [description[0] for description in cursor.description]
            recent_broadcasts = [dict(zip(columns, row)) for row in cursor.fetchall()]
            conn.close()
        except Exception as e:
            flash(f"Database error: {e}", 'error')
    
    # If no broadcasts in database, get from output folder
    if not recent_broadcasts:
        from pathlib import Path
        output_dir = Path('output')
        if output_dir.exists():
            # Get all mp3 files and create broadcast entries
            mp3_files = sorted(output_dir.glob('digest_*.mp3'), key=lambda x: x.stat().st_mtime, reverse=True)
            recent_broadcasts = []
            for mp3_file in mp3_files[:5]:  # Get last 5
                # Get corresponding markdown file
                md_file = mp3_file.with_suffix('.md')
                if md_file.exists():
                    recent_broadcasts.append({
                        'created_at': datetime.fromtimestamp(mp3_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'audio_path': str(mp3_file),
                        'file_path': str(md_file),
                        'model_used': 'File-based',
                        'article_count': 'N/A'  # Could parse from file if needed
                    })
    
    return render_template('dashboard.html',
                         recent_articles=recent_articles,
                         feed_analytics=feed_analytics,
                         recent_broadcasts=recent_broadcasts,
                         generation_status=generation_status)

@app.route('/settings')
def settings():
    """Settings page"""
    # Load current settings
    env_vars = {
        'LLM_PROVIDER': os.getenv('LLM_PROVIDER', 'ollama'),
        'OLLAMA_BASE_URL': os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
        'OPENAI_API_BASE': os.getenv('OPENAI_API_BASE', ''),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', ''),
        'SUMMARY_MODEL_CONFIG': os.getenv('SUMMARY_MODEL_CONFIG', 'default_model'),
        'BROADCAST_MODEL_CONFIG': os.getenv('BROADCAST_MODEL_CONFIG', 'broadcast_model'),
        'TTS_VOICE': os.getenv('TTS_VOICE', 'en-US-GuyNeural'),
        'DATABASE_ENABLED': os.getenv('DATABASE_ENABLED', 'true'),
        'MAX_ARTICLES_PER_FEED': os.getenv('MAX_ARTICLES_PER_FEED', '1')
    }
    
    # Load model configurations
    model_configs = {}
    try:
        model_configs = config_manager.models_config
    except Exception as e:
        flash(f"Error loading model configs: {e}", 'error')
    
    return render_template('settings.html', 
                         env_vars=env_vars, 
                         model_configs=model_configs)

@app.route('/feeds')
def feeds():
    """RSS feeds management"""
    try:
        feed_urls = load_feeds()
        db = get_database()
        
        # Get feed statistics if database is available
        feed_stats = {}
        if db:
            analytics = db.get_feed_analytics()
            for stat in analytics:
                feed_stats[stat['source_feed']] = stat
                
    except Exception as e:
        flash(f"Error loading feeds: {e}", 'error')
        feed_urls = []
        feed_stats = {}
    
    return render_template('feeds.html', 
                         feed_urls=feed_urls, 
                         feed_stats=feed_stats)

@app.route('/history')
def history():
    """Generated content history"""
    db = get_database()
    articles = []
    broadcasts = []
    
    if db:
        try:
            # Get recent articles with summaries
            import sqlite3
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT a.*, s.summary_text, s.model_used, s.created_at as summary_date
                FROM articles a
                LEFT JOIN summaries s ON a.id = s.article_id
                WHERE a.processed = TRUE
                ORDER BY a.fetched_at DESC
                LIMIT 50
            """)
            columns = [description[0] for description in cursor.description]
            articles = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Get broadcasts
            cursor.execute("""
                SELECT * FROM broadcasts 
                ORDER BY created_at DESC 
                LIMIT 20
            """)
            columns = [description[0] for description in cursor.description]
            broadcasts = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
        except Exception as e:
            flash(f"Database error: {e}", 'error')
    
    return render_template('history.html',
                         articles=articles,
                         broadcasts=broadcasts)

@app.route('/lounge')
def lounge():
    """Lounge area for viewing and playing generated content"""
    # Get recent digest files
    output_dir = Path('output')
    digest_files = []
    
    if output_dir.exists():
        # Get all markdown files (digests) and their corresponding audio files
        for md_file in sorted(output_dir.glob('digest_*.md'), key=lambda x: x.stat().st_mtime, reverse=True):
            mp3_file = md_file.with_suffix('.mp3')
            
            # Read the content
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract sources from content
                sources = extract_sources_from_content(content)
            
                digest_info = {
                    'filename': md_file.name,
                    'audio_filename': mp3_file.name if mp3_file.exists() else None,
                    'created': md_file.stat().st_mtime,
                    'size': md_file.stat().st_size,
                    'content': content,
                    'has_audio': mp3_file.exists(),
                    'sources': sources
                }
                digest_files.append(digest_info)
            except Exception as e:
                print(f"Error reading {md_file}: {e}")
    
    return render_template('lounge.html', digest_files=digest_files)

@app.route('/api/test_connection', methods=['POST'])
def api_test_connection():
    """Test LLM and database connections"""
    connection_type = request.json.get('type', 'llm')
    
    if connection_type == 'llm':
        success = test_web_llm_connection()
        return jsonify({'success': success})
    elif connection_type == 'database':
        success = test_database()
        return jsonify({'success': success})
    else:
        return jsonify({'success': False, 'error': 'Invalid connection type'})

def test_web_llm_connection():
    """Test LLM connection using current web settings"""
    try:
        # Reload environment variables from .env file
        from dotenv import load_dotenv
        load_dotenv('.env', override=True)
        
        # Get current provider setting
        provider = os.getenv('LLM_PROVIDER', 'ollama')
        print(f"Testing LLM connection...")
        print(f"Provider: {provider}")
        
        if provider == 'gemini':
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                print("❌ No Gemini API key configured")
                return False
                
            # Get the configured model from settings
            summary_model = os.getenv('SUMMARY_MODEL_CONFIG', 'gemini_flash')
            
            # Map our config names to actual Gemini model names
            model_mapping = {
                'gemini_flash': 'gemini-1.5-flash',
                'gemini_pro': 'gemini-1.5-pro',
                'default_model': 'gemini-1.5-flash'
            }
            
            actual_model = model_mapping.get(summary_model, 'gemini-1.5-flash')
            
            print(f"Testing Google Gemini connection...")
            print(f"Using model: {actual_model} (from config: {summary_model})")
            
            # Test Gemini connection
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                
                # Test with the configured model
                model = genai.GenerativeModel(actual_model)
                response = model.generate_content("Hello")
                
                print("✅ Gemini connection successful")
                return True
                
            except Exception as e:
                print(f"❌ Gemini connection failed: {e}")
                print(f"   Attempted model: {actual_model}")
                print(f"   Try checking available models at https://ai.google.dev/models")
                return False
                
        elif provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
            
            if not api_key:
                print("❌ No OpenAI API key configured")
                return False
                
            print(f"Endpoint: {api_base}")
            print(f"Testing OpenAI-compatible connection...")
            
            # Test OpenAI connection
            try:
                import openai
                client = openai.OpenAI(
                    api_key=api_key,
                    base_url=api_base
                )
                
                # Test with a simple completion
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10
                )
                
                print("✅ OpenAI connection successful")
                return True
                
            except Exception as e:
                print(f"❌ OpenAI connection failed: {e}")
                return False
                
        elif provider == 'ollama':
            base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
            model = os.getenv('SUMMARY_MODEL_CONFIG', 'mistral:latest')
            
            print(f"Model: {model}")
            print(f"Endpoint: {base_url}")
            
            # Test Ollama connection
            try:
                import ollama
                client = ollama.Client(host=base_url)
                
                # Test with a simple prompt
                response = client.generate(model=model, prompt="Hello", stream=False)
                
                print("✅ Ollama connection successful")
                return True
                
            except Exception as e:
                print(f"❌ Ollama connection failed: {e}")
                return False
        else:
            print(f"❌ Unknown provider: {provider}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return False

@app.route('/api/save_settings', methods=['POST'])
def api_save_settings():
    """Save environment settings"""
    try:
        settings_data = request.json
        print(f"Received settings data: {settings_data}")
        
        # Update .env file
        env_lines = []
        env_file_path = '.env'
        updated_keys = set()
        
        # Add/update new settings first
        for key, value in settings_data.items():
            if key.startswith('env_'):
                env_key = key[4:]  # Remove 'env_' prefix
                env_lines.append(f"{env_key}={value}")
                updated_keys.add(env_key)
                print(f"Setting {env_key} = {value}")
        
        # Read existing .env and preserve non-updated values
        if os.path.exists(env_file_path):
            with open(env_file_path, 'r') as f:
                existing_lines = f.readlines()
            
            # Keep comments and non-updated settings
            for line in existing_lines:
                line = line.strip()
                if line.startswith('#') or ('=' not in line and line):
                    env_lines.append(line)
                elif '=' in line:
                    key = line.split('=')[0]
                    if key not in updated_keys:
                        env_lines.append(line)
        
        # Write updated .env file
        with open(env_file_path, 'w') as f:
            f.write('\n'.join(env_lines) + '\n')
        
        print(f"Updated .env file with {len(updated_keys)} settings")
        
        # Reload environment variables immediately
        from dotenv import load_dotenv
        load_dotenv('.env', override=True)
        
        # Verify the setting was applied
        max_articles = os.getenv('MAX_ARTICLES_PER_FEED')
        print(f"Settings saved and reloaded. MAX_ARTICLES_PER_FEED is now: {max_articles}")
        
        return jsonify({'success': True, 'message': 'Settings saved successfully'})
    
    except Exception as e:
        print(f"Error saving settings: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save_feeds', methods=['POST'])
def api_save_feeds():
    """Save RSS feeds"""
    try:
        feeds_data = request.json.get('feeds', [])
        
        # Validate feeds
        valid_feeds = []
        for feed in feeds_data:
            if feed.strip() and feed.startswith(('http://', 'https://')):
                valid_feeds.append(feed.strip())
        
        # Save to feeds.yaml
        feeds_config = {'feeds': valid_feeds}
        with open('settings/feeds/feeds.yaml', 'w') as f:
            yaml.dump(feeds_config, f, default_flow_style=False)
        
        return jsonify({'success': True, 'message': f'Saved {len(valid_feeds)} feeds'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/generate_digest', methods=['POST'])
def api_generate_digest():
    """Start digest generation in background"""
    global generation_status
    
    if generation_status['running']:
        return jsonify({'success': False, 'error': 'Generation already in progress'})
    
    # Start background task
    thread = threading.Thread(target=background_generate_digest)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Generation started'})

@app.route('/api/generation_status')
def api_generation_status():
    """Get current generation status"""
    return jsonify(generation_status)

def background_generate_digest():
    """Background task for digest generation"""
    global generation_status
    
    generation_status['running'] = True
    generation_status['progress'] = 0
    generation_status['stage'] = 'Initializing'
    generation_status['error'] = None
    generation_status['result_file'] = None
    
    try:
        # Stage 1: Load feeds
        generation_status['stage'] = 'Loading RSS feeds'
        generation_status['progress'] = 10
        feed_urls = load_feeds()
        print(f"Loaded {len(feed_urls)} RSS feeds")
        
        # Stage 2: Fetch articles
        generation_status['stage'] = 'Fetching articles'
        generation_status['progress'] = 25
        articles = fetch_articles(feed_urls)
        
        if not articles:
            generation_status['error'] = 'No new articles found. This could be due to: 1) All articles already processed (check database), 2) Network/feed issues, 3) All feeds failing to load'
            return
        
        print(f"Found {len(articles)} new articles to process")
        
        # Stage 3: Process articles
        generation_status['stage'] = f'Processing {len(articles)} articles'
        generation_status['progress'] = 50
        summaries = extract_and_summarize_articles(articles)
        
        if not summaries:
            # Count how many articles were attempted vs successful
            total_articles = len(articles)
            generation_status['error'] = f'No articles successfully processed (0 of {total_articles}). Common causes: 1) 403/404 errors from news sites, 2) Paywall-protected articles, 3) Network connectivity issues. Try different RSS feeds or check the logs for specific errors.'
            return
        
        successful_count = len(summaries)
        total_count = len(articles)
        print(f"🔍 ARTICLE PROCESSING SUMMARY:")
        print(f"   📥 Total articles found: {total_count}")
        print(f"   ✅ Successfully processed: {successful_count}")
        print(f"   ❌ Failed/skipped: {total_count - successful_count}")
        print(f"   📊 Success rate: {(successful_count/total_count)*100:.1f}%")
        
        # Stage 4: Generate broadcast
        generation_status['stage'] = f'Generating broadcast from {successful_count} articles'
        generation_status['progress'] = 75
        broadcast = generate_broadcast_with_llm(summaries)
        
        # Stage 5: Save files
        generation_status['stage'] = 'Saving files'
        generation_status['progress'] = 90
        digest_path = save_digest(broadcast, summaries=summaries)
        
        # Stage 6: Generate audio
        generation_status['stage'] = 'Generating audio'
        generation_status['progress'] = 95
        mp3_path = digest_path.replace('.md', '.mp3')
        
        # Run TTS in async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(text_to_speech(broadcast, output_path=mp3_path))
        loop.close()
        
        # Complete
        generation_status['stage'] = 'Complete'
        generation_status['progress'] = 100
        generation_status['result_file'] = {
            'digest': digest_path,
            'audio': mp3_path
        }
        
        print(f"Generation completed successfully: {digest_path}")
        
    except Exception as e:
        generation_status['error'] = f"Generation failed: {str(e)}"
        generation_status['stage'] = 'Error'
        print(f"Generation error: {e}")
    finally:
        generation_status['running'] = False

@app.route('/api/download/<file_type>/<path:filename>')
def api_download_file(file_type, filename):
    """Download generated files"""
    try:
        if file_type in ['digest', 'audio']:
            file_path = os.path.join('output', filename)
            if os.path.exists(file_path):
                return send_file(file_path, as_attachment=True)
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics')
def api_analytics():
    """Get analytics data for dashboard"""
    db = get_database()
    if not db:
        return jsonify({'error': 'Database not enabled'})
    
    try:
        # Get various analytics
        feed_analytics = db.get_feed_analytics()
        
        # Get daily article counts for the last 7 days
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DATE(fetched_at) as date, COUNT(*) as count
            FROM articles
            WHERE fetched_at >= date('now', '-7 days')
            GROUP BY DATE(fetched_at)
            ORDER BY date
        """)
        daily_counts = [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Get model usage statistics
        cursor.execute("""
            SELECT model_used, COUNT(*) as count
            FROM summaries
            GROUP BY model_used
            ORDER BY count DESC
        """)
        model_stats = [{'model': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Get articles processed today (before closing connection)
        cursor.execute("""
            SELECT COUNT(*)
            FROM articles
            WHERE DATE(fetched_at) = DATE('now')
            AND processed = TRUE
        """)
        articles_today_count = cursor.fetchone()[0]
        
        conn.close()
        
        # Count actual broadcast files (mp3s) in output folder
        broadcast_count = 0
        try:
            from pathlib import Path
            output_dir = Path('output')
            if output_dir.exists():
                mp3_files = list(output_dir.glob('digest_*.mp3'))
                broadcast_count = len(mp3_files)
        except Exception as e:
            print(f"Error counting broadcast files: {e}")

        return jsonify({
            'feed_analytics': feed_analytics,
            'daily_counts': daily_counts,
            'model_stats': model_stats,
            'articles_today': articles_today_count,
            'broadcast_count': broadcast_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/test_feed', methods=['POST'])
def api_test_feed():
    """Test a single RSS feed"""
    try:
        data = request.json
        feed_url = data.get('url')
        
        if not feed_url:
            return jsonify({'success': False, 'error': 'No URL provided'})
        
        # Test the feed
        import feedparser
        feed = feedparser.parse(feed_url)
        
        if feed.bozo and feed.bozo_exception:
            return jsonify({
                'success': False,
                'error': f'Feed parsing error: {feed.bozo_exception}'
            })
        
        article_count = len(feed.entries)
        feed_title = getattr(feed.feed, 'title', 'Unknown Feed')
        
        return jsonify({
            'success': True,
            'articles': article_count,
            'title': feed_title,
            'last_updated': getattr(feed.feed, 'updated', None)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/cleanup_database', methods=['POST'])
def api_cleanup_database():
    """Clean up old articles from database"""
    try:
        data = request.json
        days = data.get('days', 7)  # Default to 7 days
        
        db = get_database()
        if not db:
            return jsonify({'success': False, 'error': 'Database not enabled'})
        
        # Delete old articles
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Delete articles older than specified days
        cursor.execute("""
            DELETE FROM articles
            WHERE fetched_at < datetime('now', '-{} days')
        """.format(days))
        
        deleted_articles = cursor.rowcount
        
        # Delete orphaned summaries
        cursor.execute("""
            DELETE FROM summaries
            WHERE article_id NOT IN (SELECT id FROM articles)
        """)
        
        deleted_summaries = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {deleted_articles} articles and {deleted_summaries} summaries older than {days} days'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/reset_processed', methods=['POST'])
def api_reset_processed():
    """Reset processed flag for all articles to allow reprocessing"""
    try:
        db = get_database()
        if not db:
            return jsonify({'success': False, 'error': 'Database not enabled'})
        
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Reset processed flag
        cursor.execute("UPDATE articles SET processed = FALSE")
        updated_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Reset processed flag for {updated_count} articles. They can now be reprocessed.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/wipe_database', methods=['POST'])
def api_wipe_database():
    """Nuclear option: Completely wipe the database clean"""
    try:
        data = request.json
        confirmation = data.get('confirmation', '')
        
        # Require specific confirmation text
        if confirmation != 'WIPE DATABASE':
            return jsonify({
                'success': False,
                'error': 'Invalid confirmation. Please type "WIPE DATABASE" exactly.'
            })
        
        db = get_database()
        if not db:
            return jsonify({'success': False, 'error': 'Database not enabled'})
        
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Get counts before deletion
        cursor.execute("SELECT COUNT(*) FROM articles")
        article_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM summaries")
        summary_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM broadcasts")
        broadcast_count = cursor.fetchone()[0]
        
        # Nuclear option: Drop and recreate all tables
        cursor.execute("DROP TABLE IF EXISTS articles")
        cursor.execute("DROP TABLE IF EXISTS summaries")
        cursor.execute("DROP TABLE IF EXISTS broadcasts")
        
        # Recreate tables with correct schema (matching database.py)
        cursor.executescript("""
            CREATE TABLE articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                link TEXT UNIQUE NOT NULL,
                published_date TEXT,
                source_feed TEXT NOT NULL,
                content TEXT,
                content_hash TEXT UNIQUE,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE
            );
            
            CREATE TABLE summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                summary_text TEXT NOT NULL,
                model_used TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processing_time_ms INTEGER,
                FOREIGN KEY (article_id) REFERENCES articles (id)
            );
            
            CREATE TABLE broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                broadcast_text TEXT NOT NULL,
                model_used TEXT NOT NULL,
                article_count INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_path TEXT,
                audio_path TEXT
            );
            
            CREATE TABLE feed_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                name TEXT,
                active BOOLEAN DEFAULT TRUE,
                last_fetched TIMESTAMP,
                fetch_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0
            );
            
            CREATE INDEX idx_articles_link ON articles(link);
            CREATE INDEX idx_articles_processed ON articles(processed);
            CREATE INDEX idx_summaries_article_id ON summaries(article_id);
            CREATE INDEX idx_feed_sources_url ON feed_sources(url);
        """)
        
        conn.commit()
        conn.close()
        
        print(f"🔥 NUCLEAR OPTION EXECUTED: Database completely wiped!")
        print(f"   Removed: {article_count} articles, {summary_count} summaries, {broadcast_count} broadcasts")
        
        return jsonify({
            'success': True,
            'message': f'🔥 NUCLEAR OPTION COMPLETE! Database completely wiped clean. Removed {article_count} articles, {summary_count} summaries, and {broadcast_count} broadcasts. Fresh start achieved.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
