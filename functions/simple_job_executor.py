#!/usr/bin/env python3
"""
Simple Job Executor - Integrates with existing job_scheduler system
Executes overdue jobs by calling the digest generation directly
"""

import os
import yaml
from pathlib import Path
from datetime import datetime

def execute_job_with_profile(job):
    """Execute a job using its RSS profile"""
    try:
        # Load job configuration
        os.environ['MAX_ARTICLES_PER_FEED'] = str(job['articles_per_feed'])
        os.environ['SUMMARY_MODEL_CONFIG'] = job['summary_model']
        os.environ['BROADCAST_MODEL_CONFIG'] = job['broadcast_model']
        
        # Load and set profile feeds
        feeds = load_profile_feeds(job['profile'])
        if not feeds:
            raise Exception(f"Profile '{job['profile']}' not found or has no feeds")
        
        # Update feeds.yaml with the job's profile feeds
        update_feeds_file(feeds)
        
        # Import and run digest generation
        from functions.news_digest_enhanced import (
            load_feeds, fetch_articles, extract_and_summarize_articles,
            generate_broadcast_with_llm, save_digest, text_to_speech
        )
        import asyncio
        
        print(f"🚀 Executing job: {job['name']}")
        print(f"   Profile: {job['profile']} ({len(feeds)} feeds)")
        
        # Load feeds
        feed_urls = load_feeds()
        print(f"📡 Loaded {len(feed_urls)} RSS feeds")
        
        # Fetch articles
        articles = fetch_articles(feed_urls)
        if not articles:
            raise Exception("No new articles found")
        
        # Process articles
        summaries = extract_and_summarize_articles(articles)
        if not summaries:
            raise Exception("No articles successfully processed")
        
        # Generate broadcast
        broadcast = generate_broadcast_with_llm(summaries)
        
        # Save files
        digest_path = save_digest(broadcast, summaries=summaries)
        
        # Generate audio
        mp3_path = digest_path.replace('.md', '.mp3')
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(text_to_speech(broadcast, output_path=mp3_path))
        loop.close()
        
        print(f"✅ Job completed successfully!")
        print(f"📄 Digest: {digest_path}")
        print(f"🎵 Audio: {mp3_path}")
        
        return True, {'digest': digest_path, 'audio': mp3_path}
        
    except Exception as e:
        print(f"❌ Job execution failed: {e}")
        return False, None

def load_profile_feeds(profile_name):
    """Load feeds from a profile"""
    try:
        # Get project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        profiles_file = Path(project_root) / 'settings' / 'feeds' / 'profiles.yaml'
        if not profiles_file.exists():
            return []
            
        with open(profiles_file, 'r') as f:
            profiles = yaml.safe_load(f) or {}
            
        if profile_name in profiles:
            return profiles[profile_name].get('feeds', [])
        return []
        
    except Exception as e:
        print(f"Error loading profile {profile_name}: {e}")
        return []

def update_feeds_file(feeds):
    """Update feeds.yaml with the provided feeds"""
    try:
        # Get project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        feeds_file = Path(project_root) / 'settings' / 'feeds' / 'feeds.yaml'
        feeds_file.parent.mkdir(parents=True, exist_ok=True)
        
        feeds_config = {'feeds': feeds}
        with open(feeds_file, 'w') as f:
            yaml.dump(feeds_config, f, default_flow_style=False)
        
        return True
        
    except Exception as e:
        print(f"Error updating feeds file: {e}")
        return False

def execute_overdue_jobs():
    """Execute all overdue jobs using the existing job scheduler system"""
    import sqlite3
    import fcntl
    import os
    from datetime import datetime
    from functions.job_scheduler import job_scheduler
    
    # Create lock file to prevent concurrent execution
    lock_file_path = 'job_execution.lock'
    
    try:
        # Try to acquire exclusive lock
        lock_file = open(lock_file_path, 'w')
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        
        print(f"🔒 Acquired execution lock")
        
        # Get overdue jobs
        overdue_jobs = job_scheduler._get_due_jobs()
        
        if not overdue_jobs:
            print("✅ No overdue jobs found")
            return 0
        
        print(f"🚨 Found {len(overdue_jobs)} overdue jobs")
        executed_count = 0
        
        for job in overdue_jobs:
            # Double-check job hasn't been executed by another process
            jobs_db_path = os.getenv('JOBS_DATABASE_PATH', 'data/jobs.db')
            conn = sqlite3.connect(jobs_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT enabled, last_run FROM scheduled_jobs WHERE id = ?", (job['id'],))
            result = cursor.fetchone()
            conn.close()
            
            if not result or not result[0]:  # Job disabled or not found
                print(f"⏭️ SKIPPED: {job['name']} (disabled or already processed)")
                continue
                
            # Check if job was executed very recently (within last 5 minutes)
            if result[1]:
                last_run = datetime.fromisoformat(result[1])
                now = datetime.now()
                time_diff = (now - last_run).total_seconds()
                if time_diff < 300:  # 5 minutes
                    print(f"⏭️ SKIPPED: {job['name']} (executed {time_diff:.0f}s ago)")
                    continue
            
            print(f"\n🎯 EXECUTING: {job['name']}")
            
            # Execute the job
            success, output_files = execute_job_with_profile(job)
            
            # Update job status using existing scheduler method
            job_scheduler._update_job_after_execution(job, success,
                                                    None if success else "Execution failed")
            
            if success:
                executed_count += 1
                print(f"✅ Job '{job['name']}' completed successfully!")
            else:
                print(f"❌ Job '{job['name']}' failed!")
            
            # Wait 10 seconds before checking next job to prevent race conditions
            import time
            if executed_count < len(overdue_jobs):  # Don't wait after the last job
                print(f"⏰ Waiting 10 seconds before next job...")
                time.sleep(10)
        
        print(f"\n📊 Execution Summary: {executed_count}/{len(overdue_jobs)} jobs completed successfully")
        return executed_count
        
    except (IOError, OSError):
        print("⏳ Another job execution process is already running")
        return 0
        
    finally:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()
            os.remove(lock_file_path)
        except:
            pass

if __name__ == "__main__":
    print("🤖 SIMPLE JOB EXECUTOR")
    print("=" * 50)
    execute_overdue_jobs()