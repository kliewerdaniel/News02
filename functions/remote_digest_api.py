#!/usr/bin/env python3
"""
Remote Digest API - Allows external access to generated digests
"""

import os
import json
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)

class RemoteDigestAPI:
    def __init__(self):
        self.api_enabled = False
        self.api_key = None
        self.max_digests_per_request = 10
        self.rate_limit_per_hour = 100
        self.request_log = {}  # Simple in-memory rate limiting
        
        self.load_config()
    
    def load_config(self):
        """Load API configuration from environment/settings"""
        self.api_enabled = os.getenv('REMOTE_DIGEST_API_ENABLED', 'false').lower() == 'true'
        self.api_key = os.getenv('REMOTE_DIGEST_API_KEY', '')
        self.max_digests_per_request = int(os.getenv('REMOTE_DIGEST_MAX_PER_REQUEST', '10'))
        self.rate_limit_per_hour = int(os.getenv('REMOTE_DIGEST_RATE_LIMIT', '100'))
    
    def save_config(self, enabled=None, api_key=None, max_per_request=None, rate_limit=None):
        """Save API configuration to .env file"""
        updates = {}
        
        if enabled is not None:
            updates['REMOTE_DIGEST_API_ENABLED'] = 'true' if enabled else 'false'
            self.api_enabled = enabled
            
        if api_key is not None:
            updates['REMOTE_DIGEST_API_KEY'] = api_key
            self.api_key = api_key
            
        if max_per_request is not None:
            updates['REMOTE_DIGEST_MAX_PER_REQUEST'] = str(max_per_request)
            self.max_digests_per_request = max_per_request
            
        if rate_limit is not None:
            updates['REMOTE_DIGEST_RATE_LIMIT'] = str(rate_limit)
            self.rate_limit_per_hour = rate_limit
        
        # Update .env file
        self._update_env_file(updates)
    
    def _update_env_file(self, updates):
        """Update .env file with new values"""
        env_file_path = '.env'
        env_lines = []
        updated_keys = set()
        
        # Add new settings first
        for key, value in updates.items():
            env_lines.append(f"{key}={value}")
            updated_keys.add(key)
        
        # Read existing .env and preserve non-updated values
        if os.path.exists(env_file_path):
            with open(env_file_path, 'r') as f:
                existing_lines = f.readlines()
            
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
    
    def generate_api_key(self):
        """Generate a secure API key"""
        return secrets.token_urlsafe(32)
    
    def validate_api_key(self, provided_key):
        """Validate provided API key"""
        if not self.api_enabled or not self.api_key:
            return False
        return provided_key == self.api_key
    
    def check_rate_limit(self, client_ip):
        """Simple rate limiting check"""
        if not self.api_enabled:
            return False
            
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        # Clean old entries
        self.request_log = {
            ip: [req_time for req_time in times if req_time > hour_ago]
            for ip, times in self.request_log.items()
        }
        
        # Check current client
        client_requests = self.request_log.get(client_ip, [])
        if len(client_requests) >= self.rate_limit_per_hour:
            return False
            
        # Add current request
        if client_ip not in self.request_log:
            self.request_log[client_ip] = []
        self.request_log[client_ip].append(now)
        
        return True
    
    def get_available_digests(self, limit=None, order='newest', profile_filter=None):
        """Get list of available digest files, optionally filtered by RSS profile"""
        output_dir = Path('output')
        if not output_dir.exists():
            return []
        
        # Get all digest markdown files
        digest_files = list(output_dir.glob('digest_*.md'))
        
        # Filter by profile if specified
        if profile_filter:
            filtered_files = []
            for md_file in digest_files:
                profile_used = self._extract_profile_from_digest(md_file)
                if profile_used and profile_used.lower() == profile_filter.lower():
                    filtered_files.append(md_file)
            digest_files = filtered_files
        
        # Sort by creation time
        if order == 'newest':
            digest_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        else:  # oldest
            digest_files.sort(key=lambda x: x.stat().st_mtime)
        
        # Apply limit
        if limit:
            limit = min(limit, self.max_digests_per_request)
            digest_files = digest_files[:limit]
        
        # Build digest info
        digests = []
        for md_file in digest_files:
            mp3_file = md_file.with_suffix('.mp3')
            
            digest_info = {
                'id': md_file.stem,
                'created': datetime.fromtimestamp(md_file.stat().st_mtime).isoformat(),
                'size_text': md_file.stat().st_size,
                'size_audio': mp3_file.stat().st_size if mp3_file.exists() else 0,
                'has_audio': mp3_file.exists(),
                'title': self._extract_title_from_digest(md_file),
                'profile_used': self._extract_profile_from_digest(md_file)
            }
            
            # Try to get audio duration if available
            if mp3_file.exists():
                digest_info['duration_seconds'] = self._get_audio_duration(mp3_file)
            
            digests.append(digest_info)
        
        return digests
    
    def _extract_title_from_digest(self, md_file):
        """Extract title from digest markdown file"""
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for first # heading
            lines = content.split('\n')
            for line in lines:
                if line.startswith('# '):
                    return line[2:].strip()
            
            # Fallback to filename-based title
            timestamp = md_file.stem.replace('digest_', '')
            return f"News Digest {timestamp}"
            
        except Exception:
            return f"Digest {md_file.stem}"
    
    def _get_audio_duration(self, mp3_file):
        """Get audio duration in seconds (basic estimate)"""
        try:
            # Simple estimate: assume 160kbps average bitrate
            file_size = mp3_file.stat().st_size
            estimated_duration = file_size / (160 * 1024 / 8)  # bytes to seconds
            return int(estimated_duration)
        except Exception:
            return 0
    
    def get_server_stats(self):
        """Get server statistics"""
        output_dir = Path('output')
        if not output_dir.exists():
            return {
                'total_text_digests': 0,
                'total_audio_digests': 0,
                'latest_digest': None,
                'total_size_mb': 0
            }
        
        text_files = list(output_dir.glob('digest_*.md'))
        audio_files = list(output_dir.glob('digest_*.mp3'))
        
        total_size = sum(f.stat().st_size for f in text_files + audio_files)
        
        latest_digest = None
        if text_files:
            latest_file = max(text_files, key=lambda x: x.stat().st_mtime)
            latest_digest = datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat()
        
        return {
            'total_text_digests': len(text_files),
            'total_audio_digests': len(audio_files),
            'latest_digest': latest_digest,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }
    
    def get_digest_content(self, digest_id, content_type='text'):
        """Get digest content (text or audio path)"""
        output_dir = Path('output')
        
        if content_type == 'text':
            file_path = output_dir / f"{digest_id}.md"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        elif content_type == 'audio':
            file_path = output_dir / f"{digest_id}.mp3"
            if file_path.exists():
                return str(file_path)
        
        return None
    
    def _extract_profile_from_digest(self, md_file):
        """Extract RSS profile name from digest file"""
        try:
            filename = md_file.stem
            
            # Method 1: Check if filename starts with profile name (new format)
            # Pattern: ProfileName_YYYY-MM-DD_HH-MM-SS
            if '_' in filename and not filename.startswith('digest_'):
                parts = filename.split('_')
                if len(parts) >= 3:  # ProfileName_YYYY-MM-DD_HH-MM-SS
                    potential_profile = parts[0]
                    if self._is_valid_profile_name(potential_profile):
                        return potential_profile
            
            # Method 2: Extract from file content metadata
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            for line in lines[:15]:  # Check first 15 lines for metadata
                line = line.strip()
                
                if line.startswith('RSS Profile:'):
                    profile = line.split(':', 1)[1].strip()
                    return profile
                elif line.startswith('Profile:'):
                    profile = line.split(':', 1)[1].strip()
                    if profile != 'Default':
                        return profile
            
            # Method 3: Check job execution database
            profile = self._get_profile_from_job_database(md_file)
            if profile:
                return profile
            
            # If no profile found, return None (default/mixed profile)
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting profile from {md_file}: {e}")
            return None
    
    def _get_profile_from_job_database(self, md_file):
        """Get profile from job execution database by matching output file"""
        try:
            import sqlite3
            db_path = 'jobs.db'
            if not os.path.exists(db_path):
                return None
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Look for job execution that created this file
            cursor.execute("""
                SELECT sj.profile
                FROM job_executions je
                JOIN scheduled_jobs sj ON je.job_id = sj.id
                WHERE je.output_file = ? OR je.output_file LIKE ?
            """, (str(md_file), f"%{md_file.name}"))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0]
            
            return None
            
        except Exception as e:
            logger.debug(f"Error checking job database for {md_file}: {e}")
            return None
    
    def _is_valid_profile_name(self, name):
        """Check if a name looks like a valid profile name"""
        # Simple validation - profile names are usually alphanumeric with common separators
        import re
        return bool(re.match(r'^[a-zA-Z0-9_\-\s]+$', name)) and len(name) > 0 and len(name) < 50
    
    def get_available_profiles(self):
        """Get list of all RSS profiles from saved profiles and used in digests"""
        profiles = set()
        
        # First, get profiles from the profiles.yaml file (these are the actual saved profiles)
        try:
            import yaml
            profiles_file = Path('settings/feeds/profiles.yaml')
            if profiles_file.exists():
                with open(profiles_file, 'r') as f:
                    saved_profiles = yaml.safe_load(f) or {}
                for profile_name in saved_profiles.keys():
                    profiles.add(profile_name)
        except Exception as e:
            logger.debug(f"Error loading profiles.yaml: {e}")
        
        # Then, check which profiles have actually been used in digests
        output_dir = Path('output')
        if output_dir.exists():
            digest_files = list(output_dir.glob('*.md'))  # Check all markdown files
            
            for md_file in digest_files:
                profile = self._extract_profile_from_digest(md_file)
                if profile:
                    profiles.add(profile)
        
        return sorted(list(profiles))
    
    def get_profile_stats(self):
        """Get statistics about digests per profile"""
        output_dir = Path('output')
        if not output_dir.exists():
            return {}
        
        profile_stats = {}
        digest_files = list(output_dir.glob('*.md'))  # Check all markdown files
        
        for md_file in digest_files:
            profile = self._extract_profile_from_digest(md_file) or 'Default'
            
            if profile not in profile_stats:
                profile_stats[profile] = {
                    'count': 0,
                    'total_size': 0,
                    'latest_digest': None
                }
            
            profile_stats[profile]['count'] += 1
            profile_stats[profile]['total_size'] += md_file.stat().st_size
            
            # Track latest digest
            digest_time = datetime.fromtimestamp(md_file.stat().st_mtime)
            if (profile_stats[profile]['latest_digest'] is None or
                digest_time > datetime.fromisoformat(profile_stats[profile]['latest_digest'])):
                profile_stats[profile]['latest_digest'] = digest_time.isoformat()
        
        # Ensure all saved profiles appear in stats, even if they have 0 digests
        available_profiles = self.get_available_profiles()
        for profile in available_profiles:
            if profile not in profile_stats:
                profile_stats[profile] = {
                    'count': 0,
                    'total_size': 0,
                    'latest_digest': None
                }
        
        return profile_stats

# Global instance
remote_api = RemoteDigestAPI()

def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not remote_api.api_enabled:
            return jsonify({'error': 'Remote Digest API is disabled'}), 403
        
        api_key = request.headers.get('X-API-Key')
        if not api_key or not remote_api.validate_api_key(api_key):
            return jsonify({'error': 'Invalid or missing API key'}), 401
        
        client_ip = request.remote_addr
        if not remote_api.check_rate_limit(client_ip):
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        return f(*args, **kwargs)
    return decorated_function