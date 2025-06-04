#!/usr/bin/env python3
"""
News02 CLI Utility
Provides command-line tools for managing the news digest system
"""

import argparse
import os
import sys
import logging
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from functions.config_manager import config_manager
from functions.llm_client import LLMFactory
from functions.database import NewsDatabase

def setup_logging(verbose=False):
    """Setup logging for CLI"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )

def test_llm_connection():
    """Test LLM provider connection"""
    print(f"Testing LLM connection...")
    print(f"Provider: {config_manager.llm_provider}")
    
    try:
        # Get default model config
        model_config = config_manager.get_model_config('default_model')
        print(f"Model: {model_config.model}")
        print(f"Endpoint: {model_config.api_endpoint}")
        
        # Create client and test
        client = LLMFactory.create_client(config_manager.llm_provider)
        
        test_messages = [
            {"role": "user", "content": "Say 'Hello, News02!' if you can hear me."}
        ]
        
        response = client.chat_completion(test_messages, model_config)
        print(f"✅ Response: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_database():
    """Test database connection and operations"""
    print("Testing database connection...")
    
    try:
        db_config = config_manager.get_database_config()
        if not db_config['enabled']:
            print("⚠️ Database is disabled in configuration")
            return True
            
        db = NewsDatabase(db_config['path'])
        
        # Test basic operations
        test_article = {
            'title': 'Test Article',
            'link': 'https://example.com/test',
            'published': '2024-01-01',
            'source_feed': 'test_feed',
            'content': 'This is a test article content.'
        }
        
        article_id = db.store_article(test_article)
        if article_id:
            print(f"✅ Database test successful (article ID: {article_id})")
            
            # Clean up test data
            import sqlite3
            conn = sqlite3.connect(db_config['path'])
            cursor = conn.cursor()
            cursor.execute("DELETE FROM articles WHERE id = ?", (article_id,))
            conn.commit()
            conn.close()
        else:
            print("✅ Database test successful (duplicate handling)")
            
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def list_models():
    """List available model configurations"""
    print("Available model configurations:")
    print("-" * 40)
    
    try:
        for name, config in config_manager.models_config.items():
            print(f"📄 {name}")
            print(f"   Model: {config.model}")
            print(f"   Endpoint: {config.api_endpoint}")
            print(f"   Temperature: {config.temperature}")
            print(f"   Max Tokens: {config.max_tokens}")
            if config.top_p:
                print(f"   Top P: {config.top_p}")
            print()
            
    except Exception as e:
        print(f"❌ Error loading models: {e}")

def show_config():
    """Show current configuration"""
    print("Current Configuration:")
    print("=" * 40)
    
    print(f"LLM Provider: {config_manager.llm_provider}")
    
    # Database config
    db_config = config_manager.get_database_config()
    print(f"Database: {'Enabled' if db_config['enabled'] else 'Disabled'}")
    if db_config['enabled']:
        print(f"Database Path: {db_config['path']}")
    
    # Output config
    output_config = config_manager.get_output_config()
    print(f"Output Directory: {output_config['directory']}")
    print(f"Max Articles per Feed: {output_config['max_articles_per_feed']}")
    
    # TTS config
    tts_config = config_manager.get_tts_config()
    print(f"TTS Voice: {tts_config['voice']}")
    
    # Model configs
    summary_model = os.getenv('SUMMARY_MODEL_CONFIG', 'default_model')
    broadcast_model = os.getenv('BROADCAST_MODEL_CONFIG', 'broadcast_model')
    print(f"Summary Model Config: {summary_model}")
    print(f"Broadcast Model Config: {broadcast_model}")

def show_analytics():
    """Show database analytics"""
    try:
        db_config = config_manager.get_database_config()
        if not db_config['enabled']:
            print("Database is disabled - no analytics available")
            return
            
        db = NewsDatabase(db_config['path'])
        analytics = db.get_feed_analytics()
        
        if not analytics:
            print("No data available for analytics")
            return
            
        print("Feed Analytics:")
        print("=" * 60)
        print(f"{'Feed':<40} {'Articles':<10} {'Last Article':<15}")
        print("-" * 60)
        
        for feed_data in analytics:
            feed_name = feed_data['source_feed'].split('/')[-1][:35]
            print(f"{feed_name:<40} {feed_data['article_count']:<10} {feed_data['last_article'][:15]:<15}")
            
    except Exception as e:
        print(f"❌ Error getting analytics: {e}")

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="News02 CLI Utility")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Test commands
    subparsers.add_parser("test-llm", help="Test LLM provider connection")
    subparsers.add_parser("test-db", help="Test database connection")
    subparsers.add_parser("test-all", help="Run all tests")
    
    # Info commands
    subparsers.add_parser("config", help="Show current configuration")
    subparsers.add_parser("models", help="List available model configurations")
    subparsers.add_parser("analytics", help="Show database analytics")
    
    # Management commands
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old database entries")
    cleanup_parser.add_argument("--days", type=int, default=30, help="Days to keep (default: 30)")
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    if args.command == "test-llm":
        test_llm_connection()
    elif args.command == "test-db":
        test_database()
    elif args.command == "test-all":
        print("Running all tests...\n")
        llm_ok = test_llm_connection()
        print()
        db_ok = test_database()
        print()
        if llm_ok and db_ok:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed")
            sys.exit(1)
    elif args.command == "config":
        show_config()
    elif args.command == "models":
        list_models()
    elif args.command == "analytics":
        show_analytics()
    elif args.command == "cleanup":
        try:
            db_config = config_manager.get_database_config()
            if db_config['enabled']:
                db = NewsDatabase(db_config['path'])
                db.cleanup_old_data(args.days)
                print(f"✅ Cleaned up data older than {args.days} days")
            else:
                print("Database is disabled")
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()