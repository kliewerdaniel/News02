import sqlite3
import json
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml
import asyncio
import os

logger = logging.getLogger(__name__)

class JobScheduler:
    def __init__(self, db_path='jobs.db'):
        self.db_path = db_path
        self.running = False
        self.current_job = None
        self.job_queue = []
        self.execution_status = {
            'running': False,
            'current_job': None,
            'progress': 0,
            'stage': 'idle',
            'error': None
        }
        self.init_database()
        
    def init_database(self):
        """Initialize the jobs database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS scheduled_jobs (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                time TEXT NOT NULL,
                profile TEXT NOT NULL,
                articles_per_feed INTEGER DEFAULT 1,
                summary_model TEXT DEFAULT 'default_model',
                broadcast_model TEXT DEFAULT 'broadcast_model',
                recurrence TEXT DEFAULT 'once',
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                run_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                last_error TEXT,
                last_output TEXT
            );
            
            CREATE TABLE IF NOT EXISTS job_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                status TEXT DEFAULT 'running',
                error_message TEXT,
                output_file TEXT,
                audio_file TEXT,
                article_count INTEGER,
                FOREIGN KEY (job_id) REFERENCES scheduled_jobs (id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_jobs_next_run ON scheduled_jobs(next_run);
            CREATE INDEX IF NOT EXISTS idx_jobs_enabled ON scheduled_jobs(enabled);
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Job scheduler database initialized: {self.db_path}")
    
    def create_job(self, job_data: Dict[str, Any]) -> str:
        """Create a new scheduled job"""
        import uuid
        job_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Calculate next run time
            next_run = self._calculate_next_run(job_data['time'], job_data['recurrence'])
            
            cursor.execute("""
                INSERT INTO scheduled_jobs 
                (id, name, time, profile, articles_per_feed, summary_model, 
                 broadcast_model, recurrence, enabled, next_run)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id, job_data['name'], job_data['time'], job_data['profile'],
                job_data['articles_per_feed'], job_data['summary_model'],
                job_data['broadcast_model'], job_data['recurrence'], 
                job_data['enabled'], next_run
            ))
            
            conn.commit()
            logger.info(f"Created job: {job_id} - {job_data['name']}")
            return job_id
            
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_jobs(self) -> List[Dict[str, Any]]:
        """Get all scheduled jobs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM scheduled_jobs 
            ORDER BY next_run ASC
        """)
        
        columns = [description[0] for description in cursor.description]
        jobs = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        
        return jobs
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific job by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM scheduled_jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            job = dict(zip(columns, row))
        else:
            job = None
            
        conn.close()
        return job
    
    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update a job"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Build update query dynamically
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key in ['name', 'time', 'profile', 'articles_per_feed', 'summary_model', 
                          'broadcast_model', 'recurrence', 'enabled', 'next_run', 'last_run',
                          'run_count', 'success_count', 'last_error', 'last_output']:
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
            
            if not set_clauses:
                return False
                
            values.append(job_id)
            
            cursor.execute(f"""
                UPDATE scheduled_jobs 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """, values)
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Delete executions first (foreign key constraint)
            cursor.execute("DELETE FROM job_executions WHERE job_id = ?", (job_id,))
            executions_deleted = cursor.rowcount
            
            # Delete the job
            cursor.execute("DELETE FROM scheduled_jobs WHERE id = ?", (job_id,))
            job_deleted = cursor.rowcount
            
            conn.commit()
            
            if job_deleted > 0:
                logger.info(f"Deleted job: {job_id} (and {executions_deleted} executions)")
                return True
            else:
                logger.warning(f"Job not found: {job_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def toggle_job(self, job_id: str, enabled: bool) -> bool:
        """Enable or disable a job"""
        updates = {'enabled': enabled}
        
        if enabled:
            # Recalculate next run when enabling
            job = self.get_job(job_id)
            if job:
                next_run = self._calculate_next_run(job['time'], job['recurrence'])
                updates['next_run'] = next_run
        else:
            updates['next_run'] = None
            
        return self.update_job(job_id, updates)
    
    def run_job_immediately(self, job_id: str) -> bool:
        """Add job to execution queue for immediate run"""
        job = self.get_job(job_id)
        if not job:
            return False
            
        # Add to queue if not already running
        if not any(q['id'] == job_id for q in self.job_queue):
            self.job_queue.append(job)
            logger.info(f"Added job {job_id} to immediate execution queue")
            return True
        
        return False
    
    def start_scheduler(self):
        """Start the job scheduler"""
        if self.running:
            return
            
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("Job scheduler started")
    
    def stop_scheduler(self):
        """Stop the job scheduler"""
        self.running = False
        logger.info("Job scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Process immediate queue first
                if self.job_queue and not self.execution_status['running']:
                    job = self.job_queue.pop(0)
                    self._execute_job(job)
                
                # Check for scheduled jobs
                if not self.execution_status['running']:
                    due_jobs = self._get_due_jobs()
                    if due_jobs:
                        self._execute_job(due_jobs[0])
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _get_due_jobs(self) -> List[Dict[str, Any]]:
        """Get jobs that are due to run"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            SELECT * FROM scheduled_jobs 
            WHERE enabled = TRUE 
            AND next_run IS NOT NULL 
            AND next_run <= ?
            ORDER BY next_run ASC
        """, (now,))
        
        columns = [description[0] for description in cursor.description]
        jobs = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        
        return jobs
    
    def _execute_job(self, job: Dict[str, Any]):
        """Execute a job"""
        job_id = job['id']
        
        try:
            self.execution_status.update({
                'running': True,
                'current_job': job['name'],
                'progress': 0,
                'stage': 'Starting',
                'error': None
            })
            
            logger.info(f"Starting job execution: {job['name']} ({job_id})")
            
            # Record execution start
            execution_id = self._start_job_execution(job_id)
            
            # Load the RSS profile
            self.execution_status.update({'progress': 10, 'stage': 'Loading RSS profile'})
            profile_feeds = self._load_profile_feeds(job['profile'])
            
            if not profile_feeds:
                raise Exception(f"Profile '{job['profile']}' not found or has no feeds")
            
            # Set environment variables for this job
            self._set_job_environment(job)
            
            # Import digest generation functions
            from functions.news_digest_enhanced import (
                fetch_articles, extract_and_summarize_articles,
                generate_broadcast_with_llm, save_digest, text_to_speech
            )
            
            # Fetch articles
            self.execution_status.update({'progress': 25, 'stage': 'Fetching articles'})
            articles = fetch_articles(profile_feeds)
            
            if not articles:
                raise Exception("No new articles found")
            
            # Process articles
            self.execution_status.update({
                'progress': 50, 
                'stage': f'Processing {len(articles)} articles'
            })
            summaries = extract_and_summarize_articles(articles)
            
            if not summaries:
                raise Exception("No articles successfully processed")
            
            # Generate broadcast
            self.execution_status.update({
                'progress': 75, 
                'stage': f'Generating broadcast from {len(summaries)} articles'
            })
            broadcast = generate_broadcast_with_llm(summaries)
            
            # Save files
            self.execution_status.update({'progress': 90, 'stage': 'Saving files'})
            digest_path = save_digest(broadcast, summaries=summaries, 
                                    job_name=job['name'].replace(' ', '_'))
            
            # Generate audio
            self.execution_status.update({'progress': 95, 'stage': 'Generating audio'})
            mp3_path = digest_path.replace('.md', '.mp3')
            
            # Run TTS in async context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(text_to_speech(broadcast, output_path=mp3_path))
            loop.close()
            
            # Complete execution
            self._complete_job_execution(execution_id, 'completed', 
                                       digest_path, mp3_path, len(summaries))
            
            # Update job status
            self._update_job_after_execution(job, True)
            
            self.execution_status.update({
                'progress': 100,
                'stage': 'Complete',
                'running': False
            })
            
            logger.info(f"Job completed successfully: {job['name']}")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Job execution failed: {job['name']} - {error_msg}")
            
            if 'execution_id' in locals():
                self._complete_job_execution(execution_id, 'failed', error=error_msg)
            
            self._update_job_after_execution(job, False, error_msg)
            
            self.execution_status.update({
                'running': False,
                'stage': 'Error',
                'error': error_msg
            })
    
    def _load_profile_feeds(self, profile_name: str) -> List[str]:
        """Load feeds from a profile"""
        try:
            profiles_file = Path('settings/feeds/profiles.yaml')
            if not profiles_file.exists():
                return []
                
            with open(profiles_file, 'r') as f:
                profiles = yaml.safe_load(f) or {}
                
            if profile_name in profiles:
                return profiles[profile_name].get('feeds', [])
            return []
            
        except Exception as e:
            logger.error(f"Error loading profile {profile_name}: {e}")
            return []
    
    def _set_job_environment(self, job: Dict[str, Any]):
        """Set environment variables for job execution"""
        os.environ['MAX_ARTICLES_PER_FEED'] = str(job['articles_per_feed'])
        os.environ['SUMMARY_MODEL_CONFIG'] = job['summary_model']
        os.environ['BROADCAST_MODEL_CONFIG'] = job['broadcast_model']
    
    def _start_job_execution(self, job_id: str) -> int:
        """Record the start of job execution"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO job_executions (job_id, status)
            VALUES (?, 'running')
        """, (job_id,))
        
        execution_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return execution_id
    
    def _complete_job_execution(self, execution_id: int, status: str, 
                              output_file: str = None, audio_file: str = None, 
                              article_count: int = None, error: str = None):
        """Record job execution completion"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE job_executions 
            SET completed_at = CURRENT_TIMESTAMP,
                status = ?,
                error_message = ?,
                output_file = ?,
                audio_file = ?,
                article_count = ?
            WHERE id = ?
        """, (status, error, output_file, audio_file, article_count, execution_id))
        
        conn.commit()
        conn.close()
    
    def _update_job_after_execution(self, job: Dict[str, Any], success: bool, 
                                  error: str = None):
        """Update job after execution"""
        updates = {
            'last_run': datetime.now().isoformat(),
            'run_count': (job.get('run_count', 0) or 0) + 1
        }
        
        if success:
            updates['success_count'] = (job.get('success_count', 0) or 0) + 1
            updates['last_error'] = None
        else:
            updates['last_error'] = error
        
        # Calculate next run for recurring jobs
        if job['recurrence'] != 'once':
            updates['next_run'] = self._calculate_next_run(job['time'], job['recurrence'])
        else:
            updates['enabled'] = False
            updates['next_run'] = None
        
        self.update_job(job['id'], updates)
    
    def _calculate_next_run(self, time_str: str, recurrence: str) -> Optional[str]:
        """Calculate the next run time for a job"""
        try:
            now = datetime.now()
            target_time = datetime.strptime(time_str, '%H:%M').time()
            
            # Start with today
            next_run = datetime.combine(now.date(), target_time)
            
            # If time has already passed today, move to tomorrow
            if next_run <= now:
                next_run += timedelta(days=1)
            
            # Handle recurrence
            if recurrence == 'daily':
                # Already set correctly above
                pass
            elif recurrence == 'weekdays':
                # Monday=0, Sunday=6
                while next_run.weekday() >= 5:  # Saturday=5, Sunday=6
                    next_run += timedelta(days=1)
            elif recurrence == 'weekends':
                while next_run.weekday() < 5:  # Monday-Friday
                    next_run += timedelta(days=1)
            elif recurrence == 'once':
                # For one-time jobs, only run if in the future
                if next_run <= now:
                    return None
            
            return next_run.isoformat()
            
        except Exception as e:
            logger.error(f"Error calculating next run: {e}")
            return None
    
    def get_execution_status(self) -> Dict[str, Any]:
        """Get current execution status"""
        return {
            'status': self.execution_status,
            'queue': [{'id': job['id'], 'name': job['name'], 'profile': job['profile']} 
                     for job in self.job_queue]
        }

# Global scheduler instance
job_scheduler = JobScheduler()