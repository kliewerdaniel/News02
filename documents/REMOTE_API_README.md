# Remote Digest API Documentation

## Overview

The Remote Digest API allows external applications to securely access your News02 generated digest files via REST endpoints. This enables integration with other systems, automated digest distribution, or programmatic access to your news content.

## Features

- 🔐 **Secure API Key Authentication**
- 📊 **Server Statistics & Digest Listing** 
- 📄 **Text Content Access**
- 🎵 **Audio File Downloads**
- ⚡ **Rate Limiting & Access Control**
- 🛡️ **IP-based Request Limiting**

## Setup

### 1. Enable API in Settings

1. Go to **Settings** page in your News02 web interface
2. Scroll to **Remote Digest API** section
3. Check **"Enable Remote Digest API"**
4. Click **"Generate New Key"** to create an API key
5. **IMPORTANT**: Copy and store the API key securely - it won't be shown again!
6. Configure limits:
   - **Max Digests Per Request**: How many digests can be requested at once (1-50)
   - **Rate Limit**: Requests per hour per IP address (10-1000)
7. Click **"Save API Settings"**

### 2. Test Connection

Use the **"Test API Connection"** button to verify the API is working correctly.

## API Endpoints

All endpoints require the `X-API-Key` header with your generated API key.

### Base URL
```
http://your-server:7855/api/remote/
```

### Authentication Test
```http
POST /api/remote/auth
Headers: X-API-Key: your-api-key-here

Response:
{
  "authenticated": true,
  "server_info": {
    "name": "News02 Digest Server",
    "version": "1.0",
    "total_digests": 25
  }
}
```

### Server Statistics
```http
GET /api/remote/stats
Headers: X-API-Key: your-api-key-here

Response:
{
  "total_text_digests": 25,
  "total_audio_digests": 24,
  "latest_digest": "2025-06-05T09:30:15",
  "total_size_mb": 156.7
}
```

### List Digests
```http
GET /api/remote/digests?limit=3&order=newest&profile=Technology
Headers: X-API-Key: your-api-key-here

Parameters:
- limit: Number of digests to return (optional, max configured limit)
- order: "newest" or "oldest" (default: newest)
- profile: Filter by RSS profile name (optional)

Response:
{
  "digests": [
    {
      "id": "digest_2025-06-05_09-30-15",
      "created": "2025-06-05T09:30:15",
      "size_text": 8924,
      "size_audio": 2104832,
      "duration_seconds": 180,
      "has_audio": true,
      "title": "Morning News Digest",
      "profile_used": "Technology"
    }
  ],
  "total_available": 25,
  "profile_filter": "Technology"
}
```

### List RSS Profiles
```http
GET /api/remote/profiles
Headers: X-API-Key: your-api-key-here

Response:
{
  "profiles": ["Technology", "Sports", "Business", "General"],
  "stats": {
    "Technology": {
      "count": 15,
      "total_size": 245760,
      "latest_digest": "2025-06-05T09:30:15"
    },
    "Sports": {
      "count": 8,
      "total_size": 156420,
      "latest_digest": "2025-06-04T18:45:22"
    }
  },
  "total_profiles": 4
}
```

### Get Profile-Specific Digests
```http
GET /api/remote/profiles/Technology/digests?limit=5&order=newest
Headers: X-API-Key: your-api-key-here

Parameters:
- limit: Number of digests to return (optional)
- order: "newest" or "oldest" (default: newest)

Response:
{
  "profile": "Technology",
  "digests": [
    {
      "id": "tech_digest_2025-06-05_09-30-15",
      "created": "2025-06-05T09:30:15",
      "size_text": 8924,
      "size_audio": 2104832,
      "duration_seconds": 180,
      "has_audio": true,
      "title": "Technology News Digest",
      "profile_used": "Technology"
    }
  ],
  "total_available": 15
}
```

### Get Digest Text
```http
GET /api/remote/digest/{digest_id}/text
Headers: X-API-Key: your-api-key-here

Response:
{
  "digest_id": "digest_2025-06-05_09-30-15",
  "text": "# Morning News Digest\n\n## Technology\n..."
}
```

### Download Digest Audio
```http
GET /api/remote/digest/{digest_id}/audio
Headers: X-API-Key: your-api-key-here

Response: Binary MP3 file download
```

## Error Responses

### 401 Unauthorized
```json
{
  "error": "Invalid or missing API key"
}
```

### 403 Forbidden
```json
{
  "error": "Remote Digest API is disabled"
}
```

### 404 Not Found
```json
{
  "error": "Digest not found"
}
```

### 429 Rate Limited
```json
{
  "error": "Rate limit exceeded"
}
```

## Example Usage

### Python Client
```python
import requests

API_KEY = "your-api-key-here"
BASE_URL = "http://localhost:7855"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Get server stats
response = requests.get(f"{BASE_URL}/api/remote/stats", headers=headers)
stats = response.json()
print(f"Total digests: {stats['total_text_digests']}")

# Get available profiles
response = requests.get(f"{BASE_URL}/api/remote/profiles", headers=headers)
profiles_data = response.json()
print(f"Available profiles: {profiles_data['profiles']}")

# Get Technology digests only
response = requests.get(f"{BASE_URL}/api/remote/digests?limit=3&profile=Technology",
                       headers=headers)
tech_digests = response.json()

for digest in tech_digests['digests']:
    print(f"Tech Digest: {digest['id']} - {digest['title']} (Profile: {digest['profile_used']})")
    
    # Get text content
    text_response = requests.get(f"{BASE_URL}/api/remote/digest/{digest['id']}/text",
                                headers=headers)
    content = text_response.json()['text']
    
    # Save to file with profile prefix
    filename = f"tech_{digest['id']}.md"
    with open(filename, 'w') as f:
        f.write(content)

# Get specific profile digests using dedicated endpoint
response = requests.get(f"{BASE_URL}/api/remote/profiles/Technology/digests?limit=5",
                       headers=headers)
profile_digests = response.json()
print(f"Technology profile has {profile_digests['total_available']} digests")
```

### cURL Examples
```bash
# Test authentication
curl -X POST "http://localhost:7855/api/remote/auth" \
     -H "X-API-Key: your-api-key-here"

# Get server stats
curl "http://localhost:7855/api/remote/stats" \
     -H "X-API-Key: your-api-key-here"

# Get available RSS profiles
curl "http://localhost:7855/api/remote/profiles" \
     -H "X-API-Key: your-api-key-here"

# Get 3 newest digests (all profiles)
curl "http://localhost:7855/api/remote/digests?limit=3&order=newest" \
     -H "X-API-Key: your-api-key-here"

# Get Technology digests only
curl "http://localhost:7855/api/remote/digests?limit=3&profile=Technology" \
     -H "X-API-Key: your-api-key-here"

# Get Technology digests using dedicated endpoint
curl "http://localhost:7855/api/remote/profiles/Technology/digests?limit=5" \
     -H "X-API-Key: your-api-key-here"

# Download audio file
curl "http://localhost:7855/api/remote/digest/digest_2025-06-05_09-30-15/audio" \
     -H "X-API-Key: your-api-key-here" \
     -o "digest_2025-06-05_09-30-15.mp3"
```

## Security Considerations

### API Key Management
- **Never share your API key** in public repositories or unsecured locations
- **Regenerate keys periodically** for security
- **Use environment variables** to store keys in applications
- **Revoke access** by disabling the API or generating a new key

### Rate Limiting
- API enforces rate limits per IP address
- Default: 100 requests per hour per IP
- Adjust limits based on your usage needs
- Consider implementing client-side caching

### Network Security
- **Use HTTPS** in production (configure reverse proxy)
- **Firewall access** to restrict which IPs can access the API
- **Monitor logs** for suspicious activity

## Use Cases

### Automated Distribution
```python
# Daily digest emailer
def send_daily_digest():
    digests = get_latest_digests(limit=1)
    if digests:
        latest = digests[0]
        text_content = get_digest_text(latest['id'])
        send_email(subject=latest['title'], body=text_content)
```

### Integration with Other Systems
```python
# Post to Slack/Discord
def post_to_slack(webhook_url):
    stats = get_server_stats()
    if stats['latest_digest']:
        latest_digests = get_latest_digests(limit=1)
        digest = latest_digests[0]
        
        slack_message = {
            "text": f"📰 New digest available: {digest['title']}",
            "attachments": [{
                "fields": [
                    {"title": "Size", "value": f"{digest['size_text']} bytes", "short": True},
                    {"title": "Audio", "value": "Available" if digest['has_audio'] else "No", "short": True}
                ]
            }]
        }
        
        requests.post(webhook_url, json=slack_message)
```

### Content Management
```python
# Archive digests to cloud storage
def backup_digests():
    all_digests = get_all_digests()
    for digest in all_digests:
        # Download text and audio
        text_content = get_digest_text(digest['id'])
        audio_path = download_digest_audio(digest['id'])
        
        # Upload to S3, Google Drive, etc.
        upload_to_cloud(digest['id'], text_content, audio_path)
```

### Profile-Based Content Distribution
```python
# Distribute specific content types to different channels
def distribute_by_profile():
    # Get available profiles
    profiles = get_profiles()
    
    for profile in profiles['profiles']:
        # Get latest digest for this profile
        latest_digests = get_profile_digests(profile, limit=1, order='newest')
        
        if latest_digests and latest_digests['digests']:
            digest = latest_digests['digests'][0]
            text_content = get_digest_text(digest['id'])
            
            # Send to profile-specific channels
            if profile.lower() == 'technology':
                send_to_tech_slack(text_content)
                post_to_tech_blog(text_content)
            elif profile.lower() == 'sports':
                send_to_sports_discord(text_content)
            elif profile.lower() == 'business':
                send_to_business_email_list(text_content)

# Technology-specific digest aggregator
def get_tech_news_summary():
    tech_digests = get_profile_digests('Technology', limit=5, order='newest')
    
    summary = "📱 Latest Technology News Summary:\n\n"
    for i, digest in enumerate(tech_digests['digests'], 1):
        summary += f"{i}. {digest['title']} ({digest['created'][:10]})\n"
        
        # Get first paragraph as preview
        content = get_digest_text(digest['id'])
        first_paragraph = content.split('\n\n')[0] if content else "No content"
        summary += f"   Preview: {first_paragraph[:100]}...\n\n"
    
    return summary
```

## Complete Example Client

See `example_api_client.py` for a complete Python client implementation that demonstrates all API features.

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check API key is correct
   - Ensure API is enabled in settings
   - Verify `X-API-Key` header is set

2. **429 Rate Limited**
   - Reduce request frequency
   - Increase rate limit in settings
   - Implement exponential backoff

3. **404 Not Found**
   - Verify digest ID exists
   - Check digest listing first
   - Ensure server has digest files

4. **Connection Refused**
   - Verify server is running
   - Check firewall settings
   - Confirm port accessibility

### Debug Mode
Enable debug logging in your client to see full request/response details:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support

For issues or questions:
1. Check this documentation
2. Review server logs for errors
3. Test with the example client
4. Verify API settings in web interface
