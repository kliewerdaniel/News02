#!/usr/bin/env python3
"""
Simple Job Runner - Runs scheduled jobs by calling the digest generation directly
No complex threading, just checks for overdue jobs and runs them like manual generation
"""

import os
import sys
import time
import sqlite3
from datetime import datetime
from pathlib import Path

def load_job_config(job):
    """Set environment variables for the job"""
    os.environ['MAX_ARTICLES_PER_FEED'] = str(job['articles_per_feed'])
    os.environ['SUMMARY_MODEL_CONFIG'] = job['summary_model']
    os.environ['BROADCAST_MODEL_CONFIG'] = job['broadcast_model']

def load_profile_feeds(profile_name):
    """Load feeds from a profile"""
    try:
        import yaml
        profiles_file = Path('settings/feeds/profiles.yaml')
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

def update_feeds_for_job(profile_name):
    """Temporarily update feeds.yaml with the job's profile feeds"""
    feeds = load_profile_feeds(profile_name)
    if not feeds:
        print(f"❌ No feeds found for profile: {profile_name}")
        return False
    
    try:
        import yaml
        feeds_file = Path('settings/feeds/feeds.yaml')
        feeds_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save feeds to feeds.yaml
        feeds_config = {'feeds': feeds}
        with open(feeds_file, 'w') as f:
            yaml.dump(feeds_config, f, default_flow_style=False)
        
        print(f"✅ Loaded {len(feeds)} feeds from profile '{profile_name}'")
        return True
        
    except Exception as e:
        print(f"❌ Error updating feeds: {e}")
        return False

def run_digest_generation(job_id=None):
    """Run digest generation exactly like the manual command"""
    try:
        # Import the digest functions
        from functions.news_digest_enhanced import (
            load_feeds, fetch_articles, extract_and_summarize_articles,
            generate_broadcast_with_llm, save_digest, text_to_speech
        )
        import asyncio
        
        if job_id:
            update_job_status(job_id, "running", 10, "Loading RSS feeds")
        print("📰 Loading RSS feeds...")
        feed_urls = load_feeds()
        print(f"📡 Loaded {len(feed_urls)} RSS feeds")
        
        if job_id:
            update_job_status(job_id, "running", 25, "Fetching articles")
        print("🔍 Fetching articles...")
        articles = fetch_articles(feed_urls)
        if not articles:
            print("❌ No new articles found")
            if job_id:
                update_job_status(job_id, "failed", 0, "No articles found", "No new articles found")
            return False, None
            
        if job_id:
            update_job_status(job_id, "running", 50, f"Processing {len(articles)} articles")
        print(f"📝 Processing {len(articles)} articles...")
        summaries = extract_and_summarize_articles(articles)
        if not summaries:
            print("❌ No articles successfully processed")
            if job_id:
                update_job_status(job_id, "failed", 0, "Processing failed", "No articles successfully processed")
            return False, None
            
        if job_id:
            update_job_status(job_id, "running", 75, f"Generating broadcast from {len(summaries)} articles")
        print(f"🎙️ Generating broadcast from {len(summaries)} articles...")
        broadcast = generate_broadcast_with_llm(summaries)
        
        if job_id:
            update_job_status(job_id, "running", 90, "Saving digest")
        print("💾 Saving digest...")
        digest_path = save_digest(broadcast, summaries=summaries)
        
        if job_id:
            update_job_status(job_id, "running", 95, "Generating audio")
        print("🔊 Generating audio...")
        mp3_path = digest_path.replace('.md', '.mp3')
        
        # Run TTS
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(text_to_speech(broadcast, output_path=mp3_path))
        loop.close()
        
        if job_id:
            update_job_status(job_id, "completed", 100, "Generation completed")
        print(f"✅ Generation completed!")
        print(f"📄 Digest: {digest_path}")
        print(f"🎵 Audio: {mp3_path}")
        
        return True, {'digest': digest_path, 'audio': mp3_path}
        
    except Exception as e:
        error_msg = f"Generation failed: {e}"
        print(f"❌ {error_msg}")
        if job_id:
            update_job_status(job_id, "failed", 0, "Error", error_msg)
        import traceback
        traceback.print_exc()
        return False, None

def get_overdue_jobs():
    """Get jobs that should run now"""
    db_path = 'jobs.db'
    if not os.path.exists(db_path):
        return []
    
    try:
        conn = sqlite3.connect(db_path)
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
        
    except Exception as e:
        print(f"Error getting jobs: {e}")
        return []

def update_job_status(job_id, status, progress=0, stage="", error=None):
    """Update job execution status for web interface monitoring"""
    try:
        conn = sqlite3.connect('jobs.db')
        cursor = conn.cursor()
        
        # Create execution status table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_execution_status (
                job_id TEXT PRIMARY KEY,
                status TEXT,
                progress INTEGER,
                stage TEXT,
                error TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            INSERT OR REPLACE INTO job_execution_status
            (job_id, status, progress, stage, error, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (job_id, status, progress, stage, error, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error updating job status: {e}")

def mark_job_completed(job_id, success, output_files=None):
    """Mark a job as completed and calculate next run"""
    try:
        conn = sqlite3.connect('jobs.db')
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        if success:
            # Update job as successful
            cursor.execute("""
                UPDATE scheduled_jobs
                SET last_run = ?,
                    run_count = COALESCE(run_count, 0) + 1,
                    success_count = COALESCE(success_count, 0) + 1,
                    last_error = NULL,
                    last_output = ?,
                    enabled = FALSE,
                    next_run = NULL
                WHERE id = ?
            """, (now, str(output_files) if output_files else None, job_id))
        else:
            # Update job as failed
            cursor.execute("""
                UPDATE scheduled_jobs
                SET last_run = ?,
                    run_count = COALESCE(run_count, 0) + 1,
                    last_error = 'Generation failed',
                    enabled = FALSE,
                    next_run = NULL
                WHERE id = ?
            """, (now, job_id))
        
        # Clear execution status
        cursor.execute("DELETE FROM job_execution_status WHERE job_id = ?", (job_id,))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error updating job: {e}")

def run_jobs():
    """Main job runner function"""
    print("🔍 Checking for overdue jobs...")
    
    overdue_jobs = get_overdue_jobs()
    if not overdue_jobs:
        print("✅ No overdue jobs found")
        return
    
    print(f"🚨 Found {len(overdue_jobs)} overdue jobs")
    
    for job in overdue_jobs:
        print(f"\n🎯 RUNNING JOB: {job['name']}")
        print(f"   Profile: {job['profile']}")
        print(f"   Articles per feed: {job['articles_per_feed']}")
        print(f"   Models: {job['summary_model']} / {job['broadcast_model']}")
        
        # Load job configuration
        load_job_config(job)
        
        # Update feeds for this job's profile
        if not update_feeds_for_job(job['profile']):
            print(f"❌ Failed to load profile feeds")
            mark_job_completed(job['id'], False)
            continue
        
        # Run the digest generation
        success = run_digest_generation()
        
        # Mark job as completed
        mark_job_completed(job['id'], success)
        
        if success:
            print(f"✅ Job '{job['name']}' completed successfully!")
        else:
            print(f"❌ Job '{job['name']}' failed!")

if __name__ == "__main__":
    print("🤖 SIMPLE JOB RUNNER")
    print("=" * 50)
    print("This script checks for overdue jobs and runs digest generation")
    print("Run this script manually or via cron for scheduled execution")
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--loop":
        print("🔄 Running in loop mode (check every 60 seconds)")
        while True:
            try:
                run_jobs()
                print("\n⏰ Waiting 60 seconds...")
                time.sleep(60)
            except KeyboardInterrupt:
                print("\n👋 Stopping job runner")
                break
    else:
        print("🔍 Single check mode")
        run_jobs()
        print("\n💡 To run continuously: python simple_job_runner.py --loop")