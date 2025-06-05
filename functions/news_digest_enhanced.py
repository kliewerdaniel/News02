#!/usr/bin/env python3
"""
Enhanced News Digest Generator with Multi-Provider LLM Support
Supports Ollama, OpenAI-compatible APIs, and Google Gemini
"""

import os
import yaml
import feedparser
from newspaper import Article
from datetime import datetime
import asyncio
import edge_tts
import logging
from tqdm import tqdm
import time
from typing import List, Dict, Any, Optional

# Import custom modules
from functions.config_manager import config_manager, ModelConfig
from functions.llm_client import LLMFactory, retry_with_backoff
from functions.database import NewsDatabase

# Setup logging
logger = logging.getLogger(__name__)

# Initialize components
llm_client = LLMFactory.create_client(config_manager.llm_provider)
db_config = config_manager.get_database_config()
database = NewsDatabase(db_config['path']) if db_config['enabled'] else None

def load_feeds(config_path: str = None) -> List[str]:
    """Load feed URLs from YAML configuration"""
    if config_path is None:
        config_path = config_manager.get_feeds_config_path()
    
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        feeds = config.get('feeds', [])
        logger.info(f"Loaded {len(feeds)} RSS feeds from {config_path}")
        return feeds
    except FileNotFoundError:
        logger.error(f"Feed configuration file not found: {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing feed configuration: {e}")
        raise

def fetch_articles(feed_urls: List[str], max_articles: int = None) -> List[Dict[str, Any]]:
    """Fetch and parse articles from RSS feeds with database integration"""
    if max_articles is None:
        output_config = config_manager.get_output_config()
        max_articles = output_config['max_articles_per_feed']
    
    articles = []
    logger.info(f"Fetching articles from {len(feed_urls)} feeds...")
    
    for url in tqdm(feed_urls, desc="Scraping feeds", unit="feed"):
        try:
            feed = feedparser.parse(url)
            
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"Feed parsing issue for {url}: {feed.bozo_exception}")
            
            feed_articles = 0
            for entry in feed.entries[:max_articles]:
                # Skip if article already exists in database
                if database and database.article_exists(entry.link):
                    continue
                
                articles.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published': entry.get('published', 'N/A'),
                    'source_feed': url
                })
                feed_articles += 1
            
            # Update feed statistics
            if database:
                database.update_feed_stats(url, success=True)
            
            logger.debug(f"Fetched {feed_articles} new articles from {url}")
            
        except Exception as e:
            logger.error(f"Error fetching feed {url}: {e}")
            if database:
                database.update_feed_stats(url, success=False)
            continue
    
    logger.info(f"Total new articles found: {len(articles)}")
    return articles

@retry_with_backoff(max_retries=3)
def summarize_with_llm(text: str, model_config_name: str = None) -> str:
    """Summarize article using configured LLM provider"""
    if model_config_name is None:
        model_config_name = os.getenv('SUMMARY_MODEL_CONFIG', 'default_model')
    
    model_config = config_manager.get_model_config(model_config_name)
    
    messages = [
        {
            "role": "system",
            "content": "You are a professional news summarizer. Create concise, factual summaries focusing on key information."
        },
        {
            "role": "user", 
            "content": (
                "Summarize the following news article in 3-5 sentences, "
                "focusing on the key facts, context, and implications. "
                "Avoid speculation and opinion.\n\n"
                f"{text}\n\nSummary:"
            )
        }
    ]
    
    start_time = time.time()
    result = llm_client.chat_completion(messages, model_config)
    processing_time = int((time.time() - start_time) * 1000)
    
    logger.debug(f"Generated summary in {processing_time}ms using {model_config.model}")
    return result, processing_time

def extract_and_summarize_articles(articles: List[Dict[str, Any]], 
                                 model_config_name: str = None) -> List[Dict[str, Any]]:
    """Extract and summarize article content with database storage"""
    summaries = []
    logger.info(f"Processing {len(articles)} articles...")
    
    for article in tqdm(articles, desc="Summarizing", unit="article"):
        try:
            # Download and parse article content
            news_article = Article(article['link'])
            news_article.download()
            news_article.parse()
            
            # Validate content quality
            content = news_article.text[:2000]  # Limit content length
            if len(content.strip()) < 100:
                logger.warning(f"Article too short, skipping: {article['link']}")
                continue
            
            # Store article in database first
            article_data = {**article, 'content': content}
            article_id = None
            if database:
                article_id = database.store_article(article_data)
            
            # Generate summary
            summary, processing_time = summarize_with_llm(content, model_config_name)
            
            summary_data = {
                'title': article['title'],
                'link': article['link'],
                'published': article['published'],
                'summary': summary,
                'source_feed': article['source_feed']
            }
            summaries.append(summary_data)
            
            # Store summary in database
            if database and article_id:
                model_name = os.getenv('SUMMARY_MODEL_CONFIG', 'default_model')
                database.store_summary(article_id, summary, model_name, processing_time)
            
        except Exception as e:
            logger.error(f"Error processing article {article['link']}: {e}")
            continue
    
    logger.info(f"Successfully processed {len(summaries)} articles")
    return summaries

@retry_with_backoff(max_retries=3)
def generate_broadcast_with_llm(summaries: List[Dict[str, Any]], 
                               model_config_name: str = None) -> str:
    """Generate news broadcast using configured LLM provider"""
    if model_config_name is None:
        model_config_name = os.getenv('BROADCAST_MODEL_CONFIG', 'broadcast_model')
    
    model_config = config_manager.get_model_config(model_config_name)
    
    # Group summaries by source for better organization
    source_groups = {}
    for summary in summaries:
        source = summary['source_feed']
        if source not in source_groups:
            source_groups[source] = []
        source_groups[source].append(summary)
    
    # Create organized content
    organized_content = []
    for source, source_summaries in source_groups.items():
        source_name = source.split('/')[-1].replace('.xml', '').replace('.rss', '')
        organized_content.append(f"From {source_name}:")
        for summary in source_summaries:
            organized_content.append(f"- {summary['title']}: {summary['summary']}")
        organized_content.append("")
    
    joined_summaries = "\n".join(organized_content)
    
    messages = [
        {
            "role": "system",
            "content": "You are a professional news anchor creating clean broadcast text for text-to-speech conversion. Write naturally flowing speech without stage directions, anchor labels, or formatting markers."
        },
        {
            "role": "user",
            "content": (
                "Create a coherent news broadcast script based on the following article summaries. "
                "Weave them together into a flowing narrative, grouping related topics and "
                "keeping it informative and neutral. Include smooth transitions between topics "
                "and maintain a professional news anchor tone.\n\n"
                "IMPORTANT: Write ONLY the spoken text without any stage directions like '(Intro Music)' "
                "or anchor labels like 'Anchor:'. Just write what should be spoken naturally.\n\n"
                f"{joined_summaries}\n\nBroadcast Script:"
            )
        }
    ]
    
    start_time = time.time()
    result = llm_client.chat_completion(messages, model_config)
    processing_time = int((time.time() - start_time) * 1000)
    
    logger.info(f"Generated broadcast in {processing_time}ms using {model_config.model}")
    return result

def save_digest(digest_text: str, output_dir: str = None, summaries: List[Dict[str, Any]] = None, job_name: str = None) -> str:
    """Save full broadcast with timestamped filename and source metadata"""
    if output_dir is None:
        output_config = config_manager.get_output_config()
        output_dir = output_config['directory']
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    # Use job name if provided, otherwise default to 'digest'
    if job_name:
        # Clean job name for filename
        import re
        clean_job_name = re.sub(r'[^\w\-_]', '_', job_name)
        filename = os.path.join(output_dir, f'{clean_job_name}_{timestamp}.md')
    else:
        filename = os.path.join(output_dir, f'digest_{timestamp}.md')
    
    # Build sources section if summaries provided (as appendix metadata)
    sources_section = ""
    if summaries:
        sources_section = "\n\n---\n\n## Reference Sources\n\n"
        sources_section += "*This section contains the original articles used to generate this broadcast and is not part of the spoken content.*\n\n"
        for i, summary in enumerate(summaries, 1):
            title = summary.get('title', f'Article {i}')
            link = summary.get('link', '')
            source_feed = summary.get('source_feed', '')
            
            # Extract domain from source feed
            try:
                from urllib.parse import urlparse
                domain = urlparse(source_feed).netloc.replace('www.', '')
            except:
                domain = 'Unknown Source'
            
            sources_section += f"{i}. **{title}**\n"
            if link:
                sources_section += f"   - URL: {link}\n"
            sources_section += f"   - Source: {domain}\n\n"
    
    # Add metadata header with profile information
    article_count = len(summaries) if summaries else "Unknown"
    profile_info = f"RSS Profile: {job_name}" if job_name else "Profile: Default"
    
    metadata = f"""# News Digest - {datetime.now().strftime('%m/%d/%Y')}
News Digest - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Generated by: News02 Enhanced
{profile_info}
LLM Provider: {config_manager.llm_provider}
Articles Processed: {article_count}
Models Used:
- Summary: {os.getenv('SUMMARY_MODEL_CONFIG', 'default_model')}
- Broadcast: {os.getenv('BROADCAST_MODEL_CONFIG', 'broadcast_model')}

---

{digest_text}
{sources_section}
"""
    
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(metadata)
    
    logger.info(f"Saved digest to: {filename}")
    return filename

def clean_text_for_tts(text: str) -> str:
    """Clean broadcast text for natural TTS by removing stage directions and formatting"""
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # Remove stage directions in parentheses like "(Intro Music fades under)"
        if line.startswith('(') and line.endswith(')'):
            continue
            
        # Remove "Anchor:" prefixes - just keep the content
        if line.startswith('Anchor:'):
            cleaned_content = line.replace('Anchor:', '').strip()
            if cleaned_content:  # Only add if there's actual content
                cleaned_lines.append(cleaned_content)
            continue
            
        # Keep other content lines (like headlines, etc.)
        cleaned_lines.append(line)
    
    # Join with proper spacing for natural speech
    cleaned_text = ' '.join(cleaned_lines)
    
    # Clean up any double spaces
    import re
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    logger.debug(f"Cleaned text for TTS: {len(text)} chars -> {len(cleaned_text)} chars")
    return cleaned_text

async def text_to_speech(text: str, output_path: str, voice: str = None) -> None:
    """Convert broadcast to speech with timestamped filename"""
    if voice is None:
        tts_config = config_manager.get_tts_config()
        voice = tts_config['voice']
    
    # Clean the text for natural TTS
    cleaned_text = clean_text_for_tts(text)
    
    try:
        communicate = edge_tts.Communicate(cleaned_text, voice=voice)
        await communicate.save(output_path)
        logger.info(f"Generated TTS audio: {output_path}")
    except Exception as e:
        logger.error(f"Error generating TTS: {e}")
        raise

def print_analytics():
    """Print feed analytics if database is enabled"""
    if not database:
        return
    
    try:
        analytics = database.get_feed_analytics()
        if analytics:
            logger.info("Feed Analytics:")
            for feed_data in analytics:
                logger.info(f"  {feed_data['source_feed']}: {feed_data['article_count']} articles")
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")

async def main():
    """Enhanced main workflow with multi-provider LLM support"""
    try:
        logger.info("Starting News Digest Generation...")
        logger.info(f"LLM Provider: {config_manager.llm_provider}")
        
        # Load RSS feeds
        feed_urls = load_feeds()
        
        # Fetch articles with deduplication
        articles = fetch_articles(feed_urls)
        
        if not articles:
            logger.info("No new articles to process")
            print_analytics()
            return
        
        # Process articles
        summaries = extract_and_summarize_articles(articles)
        
        if not summaries:
            logger.warning("No articles successfully processed")
            return
        
        # Generate broadcast
        broadcast = generate_broadcast_with_llm(summaries)
        
        # Save outputs
        digest_path = save_digest(broadcast)
        
        # Generate TTS audio
        mp3_path = digest_path.replace('.md', '.mp3')
        await text_to_speech(broadcast, output_path=mp3_path)
        
        # Store broadcast in database
        if database:
            broadcast_model = os.getenv('BROADCAST_MODEL_CONFIG', 'broadcast_model')
            database.store_broadcast(broadcast, broadcast_model, len(summaries),
                                   digest_path, mp3_path)
        
        logger.info("News digest generation completed successfully!")
        print_analytics()
        
    except Exception as e:
        logger.error(f"Error in main workflow: {e}")
        raise

# Backward compatibility functions
def summarize_with_ollama(text, model=None):
    """Legacy function for backward compatibility"""
    summary, _ = summarize_with_llm(text, 'default_model')
    return summary

def generate_broadcast(summaries, model=None):
    """Legacy function for backward compatibility"""
    return generate_broadcast_with_llm(summaries, 'broadcast_model')

if __name__ == "__main__":
    asyncio.run(main())