import sqlite3
import hashlib
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class NewsDatabase:
    def __init__(self, db_path='news.db'):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS articles (
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
            
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                summary_text TEXT NOT NULL,
                model_used TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processing_time_ms INTEGER,
                FOREIGN KEY (article_id) REFERENCES articles (id)
            );
            
            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                broadcast_text TEXT NOT NULL,
                model_used TEXT NOT NULL,
                article_count INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_path TEXT,
                audio_path TEXT
            );
            
            CREATE TABLE IF NOT EXISTS feed_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                name TEXT,
                active BOOLEAN DEFAULT TRUE,
                last_fetched TIMESTAMP,
                fetch_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0
            );
            
            CREATE INDEX IF NOT EXISTS idx_articles_link ON articles(link);
            CREATE INDEX IF NOT EXISTS idx_articles_processed ON articles(processed);
            CREATE INDEX IF NOT EXISTS idx_summaries_article_id ON summaries(article_id);
            CREATE INDEX IF NOT EXISTS idx_feed_sources_url ON feed_sources(url);
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized: {self.db_path}")
    
    def article_exists(self, link: str) -> bool:
        """Check if article already exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM articles WHERE link = ?", (link,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    def store_article(self, article_data: Dict[str, Any]) -> Optional[int]:
        """Store new article with deduplication"""
        if self.article_exists(article_data['link']):
            logger.debug(f"Article already exists: {article_data['link']}")
            return None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        content = article_data.get('content', '')
        content_hash = hashlib.md5(content.encode()).hexdigest() if content else None
        
        try:
            cursor.execute("""
                INSERT INTO articles 
                (title, link, published_date, source_feed, content, content_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                article_data['title'],
                article_data['link'], 
                article_data.get('published', ''),
                article_data['source_feed'],
                content,
                content_hash
            ))
            
            article_id = cursor.lastrowid
            conn.commit()
            logger.debug(f"Stored article: {article_id}")
            return article_id
            
        except sqlite3.IntegrityError as e:
            logger.warning(f"Duplicate content detected: {e}")
            return None
        finally:
            conn.close()
    
    def get_recent_articles(self, hours: int = 24) -> List[Dict]:
        """Get articles from last N hours to avoid reprocessing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM articles
            WHERE fetched_at > datetime('now', '-{} hours')
            AND processed = FALSE
        """.format(hours))
        
        columns = [description[0] for description in cursor.description]
        articles = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return articles
    
    def get_recent_articles_for_dashboard(self, limit: int = 5) -> List[Dict]:
        """Get most recent articles for dashboard display (processed or not)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, link, published_date, source_feed, fetched_at, processed
            FROM articles
            ORDER BY fetched_at DESC
            LIMIT ?
        """, (limit,))
        
        columns = [description[0] for description in cursor.description]
        articles = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return articles
    
    def store_summary(self, article_id: int, summary_text: str, model_used: str, processing_time: int):
        """Store AI-generated summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO summaries 
                (article_id, summary_text, model_used, processing_time_ms)
                VALUES (?, ?, ?, ?)
            """, (article_id, summary_text, model_used, processing_time))
            
            # Mark article as processed
            cursor.execute("""
                UPDATE articles SET processed = TRUE WHERE id = ?
            """, (article_id,))
            
            conn.commit()
            logger.debug(f"Stored summary for article: {article_id}")
            
        except Exception as e:
            logger.error(f"Error storing summary: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def store_broadcast(self, broadcast_text: str, model_used: str, article_count: int, 
                       file_path: str, audio_path: str) -> int:
        """Store generated broadcast"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO broadcasts 
                (broadcast_text, model_used, article_count, file_path, audio_path)
                VALUES (?, ?, ?, ?, ?)
            """, (broadcast_text, model_used, article_count, file_path, audio_path))
            
            broadcast_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Stored broadcast: {broadcast_id}")
            return broadcast_id
            
        except Exception as e:
            logger.error(f"Error storing broadcast: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_feed_analytics(self) -> List[Dict]:
        """Get performance analytics for RSS feeds"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                source_feed,
                COUNT(*) as article_count,
                MAX(fetched_at) as last_article,
                COUNT(DISTINCT DATE(fetched_at)) as active_days
            FROM articles 
            GROUP BY source_feed
            ORDER BY article_count DESC
        """)
        
        columns = [description[0] for description in cursor.description]
        analytics = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return analytics
    
    def update_feed_stats(self, feed_url: str, success: bool = True):
        """Update feed fetch statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Insert or update feed source
            cursor.execute("""
                INSERT OR IGNORE INTO feed_sources (url, name) 
                VALUES (?, ?)
            """, (feed_url, feed_url.split('/')[-1]))
            
            if success:
                cursor.execute("""
                    UPDATE feed_sources 
                    SET last_fetched = CURRENT_TIMESTAMP, 
                        fetch_count = fetch_count + 1
                    WHERE url = ?
                """, (feed_url,))
            else:
                cursor.execute("""
                    UPDATE feed_sources 
                    SET error_count = error_count + 1
                    WHERE url = ?
                """, (feed_url,))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error updating feed stats: {e}")
        finally:
            conn.close()
    
    def get_article_by_id(self, article_id: int) -> Optional[Dict]:
        """Get article by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
        
        row = cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            article = dict(zip(columns, row))
        else:
            article = None
            
        conn.close()
        return article
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old data beyond specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DELETE FROM summaries 
                WHERE article_id IN (
                    SELECT id FROM articles 
                    WHERE fetched_at < datetime('now', '-{} days')
                )
            """.format(days))
            
            cursor.execute("""
                DELETE FROM articles 
                WHERE fetched_at < datetime('now', '-{} days')
            """.format(days))
            
            cursor.execute("""
                DELETE FROM broadcasts 
                WHERE created_at < datetime('now', '-{} days')
            """.format(days))
            
            conn.commit()
            logger.info(f"Cleaned up data older than {days} days")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            conn.rollback()
        finally:
            conn.close()
