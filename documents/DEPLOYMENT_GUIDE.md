# 🚀 News02 Production Deployment Guide

## 📋 **Deployment Overview**

**Target Setup:**
- **Web Interface**: `https://rss.example.com` (port 443/80)
- **API Only**: `https://rss.example.com:7855` (API endpoints only)
- **Security**: API key authentication for external access

## 🏗️ **Architecture Options**

### Option 1: Single Instance with Port Separation
```
├── Web Interface (Port 80/443)
│   ├── Full News02 dashboard
│   ├── RSS management
│   ├── Job scheduling
│   └── Lounge/History
│
└── API Only (Port 7855)
    ├── /api/remote/* endpoints only
    ├── API key required
    └── CORS configured
```

### Option 2: Separate Services
```
├── Web Service (rss.example.com)
│   └── Full dashboard interface
│
└── API Service (rss.example.com:7855)
    └── Remote Digest API only
```

## 🔧 **Configuration for Production**

### 1. Environment Variables
```bash
# Production settings
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-super-secret-production-key

# API Configuration
REMOTE_API_ENABLED=true
REMOTE_API_PORT=7855
API_DOMAIN=rss.example.com

# SSL/TLS
SSL_CERT_PATH=/etc/ssl/certs/rss.example.com.crt
SSL_KEY_PATH=/etc/ssl/private/rss.example.com.key
```

### 2. Nginx Configuration
```nginx
# Main web interface
server {
    listen 80;
    server_name rss.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name rss.example.com;
    
    ssl_certificate /etc/ssl/certs/rss.example.com.crt;
    ssl_certificate_key /etc/ssl/private/rss.example.com.key;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# API-only service
server {
    listen 7855 ssl;
    server_name rss.example.com;
    
    ssl_certificate /etc/ssl/certs/rss.example.com.crt;
    ssl_certificate_key /etc/ssl/private/rss.example.com.key;
    
    # Only allow API endpoints
    location /api/remote/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers for external API access
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "X-API-Key, Content-Type";
    }
    
    # Block all other endpoints
    location / {
        return 404;
    }
}
```

### 3. Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Create non-root user
RUN useradd -m -u 1000 news02
RUN chown -R news02:news02 /app
USER news02

EXPOSE 5000 7855

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "web_app:app"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  news02:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_ENABLED=true
      - REMOTE_API_ENABLED=true
    volumes:
      - ./output:/app/output
      - ./settings:/app/settings
      - ./data:/app/data
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
      - "7855:7855"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - news02
    restart: unless-stopped
```

## 🔐 **Security Considerations**

### API Security
```python
# Additional security for production
RATE_LIMITING = {
    'per_ip': 100,  # requests per hour per IP
    'per_key': 1000  # requests per hour per API key
}

ALLOWED_ORIGINS = [
    'https://your-trusted-domain.com',
    'https://another-trusted-app.com'
]
```

### Firewall Rules
```bash
# Allow only necessary ports
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw allow 7855  # API port
ufw enable
```

## 📡 **API Usage Examples**

### External API Access
```bash
# From external applications
curl "https://rss.example.com:7855/api/remote/stats" \
     -H "X-API-Key: your-production-api-key"

curl "https://rss.example.com:7855/api/remote/digests?profile=Tech%20Feed" \
     -H "X-API-Key: your-production-api-key"
```

### Share URLs (Production)
```javascript
// Updated share function for production
function shareBroadcast(broadcastId) {
    const shareUrl = `https://rss.example.com/broadcast/${broadcastId}`;
    
    if (navigator.share) {
        navigator.share({
            title: 'News Digest',
            text: 'Check out this news digest',
            url: shareUrl
        });
    } else {
        // Copy production URL
        navigator.clipboard.writeText(shareUrl);
    }
}
```

## 🚀 **Deployment Steps**

### 1. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip nginx docker.io docker-compose

# Clone repository
git clone <your-repo> /opt/news02
cd /opt/news02
```

### 2. SSL Certificate
```bash
# Using Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d rss.example.com
```

### 3. Launch Services
```bash
# Using Docker Compose
docker-compose up -d

# Or traditional deployment
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:5000 --workers 4 web_app:app
```

### 4. Configure API Keys
```bash
# Generate production API key via web interface
# Or via command line:
python -c "
from functions.remote_digest_api import remote_api
key = remote_api.generate_api_key()
print(f'Production API Key: {key}')
"
```

## 📊 **Monitoring & Maintenance**

### Health Checks
```bash
# Check web interface
curl -f https://rss.example.com/

# Check API
curl -f https://rss.example.com:7855/api/remote/stats \
     -H "X-API-Key: your-key"
```

### Backup Strategy
```bash
# Backup script
#!/bin/bash
tar -czf backup-$(date +%Y%m%d).tar.gz \
    output/ settings/ data/ .env
```

## 🎯 **Production Benefits**

✅ **Public accessibility** for digest sharing
✅ **Secure API access** with authentication
✅ **Professional URLs** for sharing broadcasts
✅ **Scalable architecture** with separated concerns
✅ **SSL/TLS encryption** for all communications
✅ **Rate limiting** and security controls
✅ **Proper logging** and monitoring

Your News02 system will be production-ready for `https://rss.example.com` with secure API access on port 7855!