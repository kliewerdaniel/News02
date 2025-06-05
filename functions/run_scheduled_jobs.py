#!/usr/bin/env python3
"""
Scheduled Job Runner - Run this via cron or manually
Executes overdue jobs using the integrated job system
"""

from functions.simple_job_executor import execute_overdue_jobs

if __name__ == "__main__":
    execute_overdue_jobs()