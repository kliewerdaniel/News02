Update Notes 6/5/2025:
- Working on fixing jobs, and adding an api service. Eventually this should lead to being able to propt this behind a secure proxy server, and run api requests to collect the broadcasts to then add to other external services. I have a discord bot project that could use this on top of its design to already update selected discord servers with youtube channel updates, subreddit updates, newsapi updates, and then hopefully add this news digest as a bi-daily updater as well for news on specific RSS Profiles set for Political news, Tech, and Financial updates.

<img src="https://github.com/user-attachments/assets/d38d03a3-6a7d-4617-b09c-103421e89cf9" width="49%"> <img src="https://github.com/user-attachments/assets/13e20837-117a-4a53-b8b5-0ca511b42009" width="49%">

![Screenshot_20250604_154206](https://github.com/user-attachments/assets/5b824481-329d-40fa-815b-ee3855994a4b)

![image](https://github.com/user-attachments/assets/c6112b34-8603-4f5f-8d9a-d5bd42cb2f1f)


# 📰 News02 - Professional AI News Digest System

Transform RSS feeds into personalized AI-generated news digests with professional audio narration and comprehensive source tracking. Supports multiple LLM providers with intelligent rate limiting.

## 🚀 Quick Start

### Easy Setup (Recommended)
Get up and running in minutes with automatic setup:

**Windows:** Double-click `quick_setup.bat`  
**Linux/Mac:** Run `./quick_setup.sh`

This will:
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Clone RSS feed discovery database (300+ feeds)
- ✅ Set up configuration files
- ✅ Test installation
- ✅ Show you exactly how to run the web GUI

### Manual Setup
If you prefer manual control:
```bash
python auto_setup.py
```

## 🌐 Web Dashboard

After setup, launch the modern web interface:
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Start web interface
python run_web.py

# Open: http://127.0.0.1:5000
```

## ✨ Enhanced Features

### 🤖 Multi-Provider LLM Support with Smart Rate Limiting
- **Ollama** - Local inference (Mistral, Llama, etc.)
- **OpenAI-Compatible** - vLLM, LocalAI, and other APIs
- **Google Gemini** - Cloud-based AI with intelligent rate limiting for free tier
- **Automatic Rate Management** - Prevents 429 errors with smart delays

### 🌐 Professional Web Experience
- **Real-time Dashboard** - Monitor generation progress with detailed statistics
- **News Lounge** - Comfortable viewing and listening experience
- **Feed Management** - Add, test, and organize RSS feeds with reliability testing
- **Settings Panel** - Configure LLM providers with live connection testing
- **Mobile Responsive** - Works perfectly on phones, tablets, desktops

### 🎧 News Lounge Experience
- **Audio Player** - Full HTML5 controls with progress tracking
- **Reading Mode** - Comfortable text viewing with typography optimization
- **Full-Screen Modal** - Distraction-free reading experience
- **Sources Modal** - Complete transparency with clickable article sources
- **Download Options** - Save both text and audio content

### 💾 Advanced Database Management
- **SQLite Storage** - Persistent article and summary storage
- **Real-time Analytics** - Feed performance and processing statistics
- **Smart Deduplication** - Avoid processing duplicate articles
- **History Tracking** - Browse past digests and summaries
- **Database Tools** - Reset, cleanup, and nuclear wipe options

### 🎵 Professional Audio Generation
- **Text-to-Speech** - Multiple voice options via Microsoft Edge TTS
- **News Anchor Style** - Professional broadcast format with transitions
- **Audio Player** - Play generated content with full browser controls
- **Download Options** - Save MP3 files locally

### 📋 Complete Source Transparency
- **Article Sources** - Individual article tracking with titles and URLs
- **Source Statistics** - "X articles from Y sources" with accurate counts
- **Clickable Sources** - Direct links to original articles
- **Copy Functionality** - Easy URL copying for sharing and verification

## 📊 Enhanced Web Dashboard

### Dashboard
- **Live Processing Monitor** - Real-time generation progress
- **Article Statistics** - "📥 32 found, ✅ 28 processed, ❌ 4 failed"
- **Feed Analytics** - Performance charts and success rates
- **Quick Actions** - One-click digest generation

### News Lounge
- **Digest Library** - Browse all generated content with audio indicators
- **Audio Playback** - Professional player with progress controls
- **Reading Modes** - Normal and full-screen comfortable reading
- **Sources Display** - Complete article transparency with links

### Settings
- **Provider Testing** - Live LLM and database connection validation
- **Rate Limiting** - Configure intelligent API management
- **Model Configuration** - Visual model selection and testing
- **Database Management** - Reset, cleanup, and nuclear options

### 🔍 RSS Feed Discovery Tool
- **300+ Curated Feeds** - Automatically cloned from awesome-rss-feeds repository
- **Smart Search** - Find feeds by topic, keyword, or category
- **English-Only Filter** - Focus on quality English-language sources
- **Country-Based Categories** - Browse feeds by country (US, UK, Canada, etc.)
- **Topic Categories** - Technology, News, Programming, Business, Science, and more
- **One-Click Adding** - Test and add feeds directly to your list
- **Live Feed Testing** - Verify feeds work before adding them

### Feed Management
- **Reliability Testing** - Test individual feeds before adding
- **Real-time Validation** - Instant feedback on feed health
- **Curated Sources** - Pre-tested reliable RSS feeds included
- **Error Handling** - Clear feedback on failed or blocked sources

### History & Analytics
- **Processing Statistics** - Detailed success/failure breakdowns
- **Content Archive** - Generated broadcast history with search
- **Audio Library** - Play past digests with full controls
- **Performance Tracking** - Monitor system efficiency over time

## 🔧 Configuration

### Environment Variables (.env)
```env
# LLM Provider Selection
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_api_key_here

# Rate Limiting & Processing
MAX_ARTICLES_PER_FEED=10
SUMMARY_MODEL_CONFIG=gemini_flash
BROADCAST_MODEL_CONFIG=gemini_flash

# Database & Web
DATABASE_ENABLED=true
WEB_HOST=127.0.0.1
WEB_PORT=5000

# Text-to-Speech
TTS_VOICE=en-US-GuyNeural
```

### Intelligent Rate Limiting
The system automatically manages API rate limits:
```
🔄 Gemini rate limit counter reset
🐌 Approaching rate limit. Waiting 32s to avoid 429 errors...
✅ Request successful (8/10 this minute)
```

### Model Configurations (settings/llm_settings/ai_models.yml)
```yaml
gemini_flash:
  api_endpoint: "https://generativelanguage.googleapis.com/v1beta/openai/"
  model: "gemini-1.5-flash"
  temperature: 0.7
  max_tokens: 4096

default_model:
  api_endpoint: "http://localhost:11434"
  model: "mistral:latest"
  temperature: 0.7
  max_tokens: 4096
```

### Curated RSS Feeds (feeds.yaml)
```yaml
feeds:
  - "http://feeds.bbci.co.uk/news/world/rss.xml"        # BBC World
  - "https://www.theguardian.com/world/rss"             # Guardian
  - "https://feeds.npr.org/1001/rss.xml"                # NPR News
  - "https://techcrunch.com/feed/"                      # TechCrunch
  - "http://feeds.arstechnica.com/arstechnica/index"    # Ars Technica
  - "https://www.wired.com/feed/rss"                    # Wired
  - "http://feeds.marketwatch.com/marketwatch/topstories" # MarketWatch
  - "https://feeds.feedburner.com/venturebeat/SZYF"     # VentureBeat
```

## 🛠️ Command Line Usage

For advanced users, command-line tools remain available:

```bash
# Generate digest with enhanced processing
python news_digest_enhanced.py

# Test all connections and configurations
python news_cli.py test-all

# View detailed analytics and statistics
python news_cli.py analytics

# Database management and cleanup
python news_cli.py cleanup --days 30
```

## 📁 Enhanced Project Structure

```
News02/
├── 🌐 Professional Web Interface
│   ├── web_app.py              # Enhanced Flask application
│   ├── run_web.py              # Web launcher
│   ├── templates/              # Professional HTML templates
│   │   ├── lounge.html         # News consumption interface
│   │   ├── dashboard.html      # Real-time monitoring
│   │   ├── feeds.html          # Feed discovery & management
│   │   └── settings.html       # Configuration management
│   └── static/                 # Modern CSS, JS, images
├── 🤖 Enhanced Core System
│   ├── news_digest_enhanced.py # Professional broadcast generation
│   ├── llm_client.py          # Multi-provider with rate limiting
│   ├── config_manager.py       # Advanced configuration handling
│   ├── database.py            # Enhanced SQLite integration
│   └── feed_discovery.py      # RSS feed discovery engine
├── 🔍 Feed Discovery Database
│   └── awesome-rss-feeds/     # 300+ curated feeds (auto-cloned)
├── ⚙️ Smart Configuration
│   ├── .env                   # Environment variables
│   ├── feeds.yaml             # Curated reliable RSS feeds
│   └── settings/              # Model configurations
└── 🛠️ Professional Tools
    ├── auto_setup.py          # Intelligent setup script
    ├── quick_setup.bat/.sh    # Platform launchers
    └── news_cli.py            # Enhanced command-line utilities
```

## 📚 Documentation

- **[📖 Setup Guide](README_SETUP.md)** - Detailed installation instructions
- **[🌐 Web Interface](README_WEB.md)** - Web dashboard documentation  
- **[🔧 Enhanced Features](README_ENHANCED.md)** - Advanced configuration
- **[⚡ Architecture](flow.md)** - Technical implementation details

## 🎯 Professional Workflow

1. **Setup** - Run quick setup script for automatic configuration
2. **Configure** - Set LLM provider with live connection testing
3. **Discover Feeds** - Browse 300+ curated feeds or search by topic/country
4. **Manage Feeds** - Add reliable RSS feeds with validation
5. **Generate** - Click "Generate Digest" and monitor real-time progress
6. **Experience** - Professional lounge with audio playback and source tracking
7. **Manage** - Database tools for maintenance and optimization

### 🔍 Feed Discovery Workflow
1. **Browse Categories** - Click "English Only" for quality sources or explore by topic
2. **Search & Filter** - Use keywords like "tech", "news", or select specific countries
3. **Test Feeds** - Verify feeds work before adding with built-in testing
4. **One-Click Add** - Instantly add working feeds to your collection
5. **Generate Digest** - Use your curated feed collection for personalized news

## 💡 Professional Use Cases

- **Daily News Briefing** - Comprehensive customized news summaries
- **Research Monitoring** - Track industry developments with source links
- **Content Creation** - Source material with proper attribution
- **Accessibility** - Professional audio news for all users
- **Corporate Intelligence** - Monitor multiple sources efficiently
- **Educational Content** - Teaching material with source transparency

## 🔍 System Requirements

### Minimum
- **Python 3.8+** with pip
- **2GB RAM** for basic operation
- **Internet connection** for RSS feeds and LLM APIs
- **Modern web browser** for dashboard interface

### Recommended
- **Python 3.10+** for optimal performance
- **4GB+ RAM** for faster processing
- **SSD storage** for database performance
- **Chrome/Firefox** for best web experience

### Optional Enhancements
- **Ollama** for local LLM inference
- **CUDA/ROCm** for GPU acceleration
- **Google Gemini API** for cloud processing

## 🚦 Rate Limiting & Performance

### Intelligent API Management
- **Automatic rate detection** and prevention
- **Smart delays** to avoid 429 errors
- **Free tier optimization** for Google Gemini
- **Progress monitoring** with detailed statistics

### Processing Statistics
```
🔍 ARTICLE PROCESSING SUMMARY:
   📥 Total articles found: 32
   ✅ Successfully processed: 28
   ❌ Failed/skipped: 4
   📊 Success rate: 87.5%
```

## 🆘 Support

### Quick Help
1. **Setup Issues**: Check [`README_SETUP.md`](README_SETUP.md)
2. **Web Interface**: See [`README_WEB.md`](README_WEB.md)
3. **Configuration**: Review [`.env`](.env) and [`settings/`](settings/)
4. **Testing**: Run `python news_cli.py test-all`

### Common Issues
- **Port conflicts**: Change `WEB_PORT` in `.env`
- **Import errors**: Ensure virtual environment is activated
- **LLM failures**: Test connections in Settings tab
- **Feed errors**: Validate URLs in Feeds tab

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **awesome-rss-feeds** - Curated RSS feed collection by plenaryapp
- **Ollama** - Local LLM inference platform
- **OpenAI** - API standards and models
- **Google** - Gemini AI integration
- **Microsoft** - Edge TTS service
- **Bootstrap** - Web interface framework

---

**🚀 Ready to get started?** Run the setup script and have your AI news digest system running in minutes!
