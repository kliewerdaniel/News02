#!/usr/bin/env python3
"""
News02 API-Only Server
Serves only the Remote Digest API endpoints on port 7855
Accessible externally with API key authentication
"""

import os
from flask import Flask, jsonify
from functions.remote_digest_api import require_api_key

# Import the main app to access view functions
from functions.web_server import app as main_app

# Create API-only Flask app
api_app = Flask(__name__)
api_app.secret_key = main_app.secret_key

# Copy API view functions from main app
@api_app.route('/api/remote/auth', methods=['POST'])
@require_api_key
def api_auth():
    return main_app.view_functions['api_remote_auth']()

@api_app.route('/api/remote/stats', methods=['GET'])
@require_api_key 
def api_stats():
    return main_app.view_functions['api_remote_stats']()

@api_app.route('/api/remote/digests', methods=['GET'])
@require_api_key
def api_digests():
    return main_app.view_functions['api_remote_digests']()

@api_app.route('/api/remote/profiles', methods=['GET'])
@require_api_key
def api_profiles():
    return main_app.view_functions['api_remote_profiles']()

@api_app.route('/api/remote/profiles/<profile_name>/digests', methods=['GET'])
@require_api_key
def api_profile_digests(profile_name):
    return main_app.view_functions['api_remote_profile_digests'](profile_name)

@api_app.route('/api/remote/digest/<digest_id>/text', methods=['GET'])
@require_api_key
def api_digest_text(digest_id):
    return main_app.view_functions['api_remote_digest_text'](digest_id)

@api_app.route('/api/remote/digest/<digest_id>/audio', methods=['GET'])
@require_api_key
def api_digest_audio(digest_id):
    return main_app.view_functions['api_remote_digest_audio'](digest_id)

@api_app.route('/health')
def api_health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'News02 API'})

@api_app.route('/')
def api_root():
    """API information endpoint"""
    return jsonify({
        'service': 'News02 Remote Digest API',
        'version': '1.0',
        'endpoints': [
            '/api/remote/auth',
            '/api/remote/stats', 
            '/api/remote/digests',
            '/api/remote/profiles',
            '/api/remote/digest/{id}/text',
            '/api/remote/digest/{id}/audio',
            '/health'
        ],
        'authentication': 'X-API-Key header required',
        'documentation': 'See REMOTE_API_README.md'
    })

@api_app.errorhandler(404)
def api_not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'This API server only provides Remote Digest API endpoints',
        'available_endpoints': '/api/remote/*'
    }), 404

@api_app.errorhandler(403)
def api_forbidden(error):
    return jsonify({
        'error': 'Authentication required',
        'message': 'Please provide a valid X-API-Key header'
    }), 403

if __name__ == '__main__':
    port = int(os.getenv('API_PORT', '7855'))
    
    print("🌐 News02 API Server Starting...")
    print(f"🔗 Listening on: 0.0.0.0:{port}")
    print("🔑 API Key authentication required")
    print("📡 External access enabled")
    print("📋 Available endpoints:")
    print("   - /api/remote/auth")
    print("   - /api/remote/stats")
    print("   - /api/remote/digests")
    print("   - /api/remote/profiles")
    print("   - /api/remote/digest/{id}/text")
    print("   - /api/remote/digest/{id}/audio")
    print("   - /health")
    print("\n🚀 Starting server...")
    
    # Run API server on all interfaces
    api_app.run(host='0.0.0.0', port=port, debug=False)