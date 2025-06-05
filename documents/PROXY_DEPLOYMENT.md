# 🚀 News02 Behind Proxy Server

## 📋 **Simple Proxy Setup**

**Perfect for:** Cloudflare, nginx proxy, reverse proxy setups

### 🎯 **Target Architecture**
```
Proxy Server (handles SSL/domain)
├── rss.example.com → http://localhost:5000 (full web interface)  
└── rss.example.com:7855 → http://localhost:5000/api/remote/* (API only)
```

### 🔧 **News02 Configuration**

**Keep it simple - just run:**
```bash
# Development
python web_app.py

# Production
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 web_app:app
```

**Environment variables:**
```bash
# .env
FLASK_ENV=production
REMOTE_API_ENABLED=true
# Proxy handles SSL, so no SSL config needed in News02
```

### 🌐 **Proxy Configuration**

**The proxy server handles:**
- ✅ SSL certificates and HTTPS
- ✅ Domain routing (`rss.example.com`)
- ✅ Port management (443 → 5000, 7855 → 5000)
- ✅ Security headers and rate limiting
- ✅ CORS if needed

**News02 just needs to:**
- ✅ Run on `localhost:5000` 
- ✅ Serve web interface and API endpoints
- ✅ Trust proxy headers for real IP detection

### 📱 **Smart Share Feature**

The environment-aware sharing will work perfectly:
- **Localhost development**: Copies text content
- **Production via proxy**: Shares proper `https://rss.example.com/broadcast/{id}` URLs

### 🎉 **Benefits**

- ✅ **Simple News02 deployment** - no SSL/domain complexity
- ✅ **Proxy handles security** - SSL, headers, rate limiting
- ✅ **Easy updates** - just restart News02 service
- ✅ **Clean separation** - proxy for infrastructure, News02 for application

**Your current setup is perfect for proxy-based deployment!**