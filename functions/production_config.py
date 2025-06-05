#!/usr/bin/env python3
"""
Production Configuration for News02
Handles production-specific settings and optimizations
"""

import os
from pathlib import Path

class ProductionConfig:
    """Production configuration settings"""
    
    # Domain settings
    DOMAIN = os.getenv('PRODUCTION_DOMAIN', 'rss.ecneptroject.com')
    API_PORT = os.getenv('API_PORT', '7855')
    
    # Security settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production')
    FLASK_ENV = 'production'
    DEBUG = False
    
    # SSL/HTTPS settings
    FORCE_HTTPS = os.getenv('FORCE_HTTPS', 'true').lower() == 'true'
    SSL_CERT_PATH = os.getenv('SSL_CERT_PATH', '/etc/ssl/certs/domain.crt')
    SSL_KEY_PATH = os.getenv('SSL_KEY_PATH', '/etc/ssl/private/domain.key')
    
    # API settings
    REMOTE_API_ENABLED = True
    API_RATE_LIMIT = int(os.getenv('API_RATE_LIMIT', '1000'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', '/var/log/news02/app.log')
    
    @classmethod
    def apply_config(cls, app):
        """Apply production configuration to Flask app"""
        app.config['SECRET_KEY'] = cls.SECRET_KEY
        app.config['ENV'] = cls.FLASK_ENV
        app.config['DEBUG'] = cls.DEBUG
        
        # Setup logging
        if not app.debug:
            import logging
            from logging.handlers import RotatingFileHandler
            
            # Create log directory if it doesn't exist
            log_dir = Path(cls.LOG_FILE).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                cls.LOG_FILE, maxBytes=10240000, backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(getattr(logging, cls.LOG_LEVEL))
            app.logger.addHandler(file_handler)
            app.logger.setLevel(getattr(logging, cls.LOG_LEVEL))
            app.logger.info('News02 startup')
    
    @classmethod
    def get_base_url(cls):
        """Get the production base URL"""
        return f"https://{cls.DOMAIN}"
    
    @classmethod
    def get_api_url(cls):
        """Get the production API URL"""
        return f"https://{cls.DOMAIN}:{cls.API_PORT}"
    
    @classmethod
    def is_production(cls):
        """Check if running in production mode"""
        return os.getenv('FLASK_ENV') == 'production'

def create_production_env():
    """Create a production .env file template"""
    env_content = """# Production Environment Configuration
FLASK_ENV=production
FLASK_DEBUG=False

# Domain and SSL
PRODUCTION_DOMAIN=rss.ecneptroject.com
API_PORT=7855
FORCE_HTTPS=true
SSL_CERT_PATH=/etc/ssl/certs/rss.ecneptroject.com.crt
SSL_KEY_PATH=/etc/ssl/private/rss.ecneptroject.com.key

# Security
SECRET_KEY=generate-a-strong-random-key-here

# Database
DATABASE_ENABLED=true
DATABASE_PATH=data/news02_production.db

# API
REMOTE_API_ENABLED=true
API_RATE_LIMIT=1000

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/news02/app.log

# LLM Configuration (adjust as needed)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
"""
    
    with open('.env.production', 'w') as f:
        f.write(env_content)
    
    print("Created .env.production template")
    print("Please customize the values for your production environment")

if __name__ == '__main__':
    create_production_env()