Update Notes 6/6/2025:
- Trying to completely seperate Web and Jobs servers, and fix logic on web to not crash when a job is completed sometimes. Additionally because they will now be seperated in an incoming update, the user will be able to turn off the webserver and only run the job and api servers. Additionally looking into API server adding some security logic. Still recommend if you do post it publicly to put it behind a proxy with SSL, and some security servers to avoid malicious probing.
- Additionally working on an apk proof-of-concept android app to mimmick the lounge page look for a client connecting and using the API server remotely.

Update Notes 6/5/2025:
- Added API server, and fixed jobs by adding an additional jobs server that will check forjobs to do every 10 minutes. This is officially finished the first full version of features, and here on will just be refactoring, optimizing, and fixing bugs.

<img src="https://github.com/user-attachments/assets/d38d03a3-6a7d-4617-b09c-103421e89cf9" width="49%"> <img src="https://github.com/user-attachments/assets/13e20837-117a-4a53-b8b5-0ca511b42009" width="49%">

![Screenshot_20250604_154206](https://github.com/user-attachments/assets/5b824481-329d-40fa-815b-ee3855994a4b)

![image](https://github.com/user-attachments/assets/c6112b34-8603-4f5f-8d9a-d5bd42cb2f1f)


# 📰 News02 - Professional AI News Digest System

Transform RSS feeds into personalized AI-generated news digests with professional audio narration and comprehensive source tracking. Supports multiple LLM providers with intelligent rate limiting.

## 🚀 Quick Start

Get your News02 system running in minutes with these simple steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ETomberg391/News02 
    cd News02
    ```
2.  **Run the quick setup script:**
    *   **Windows:** Double-click `quick_setup.bat`
    *   **Linux/Mac:** Run `./quick_setup.sh`
    This script will automatically create a virtual environment, install dependencies, clone the RSS feed discovery database, and set up configuration files.

3.  **Activate the virtual environment:**
    *   **Linux/Mac:** `source venv/bin/activate`
    *   **Windows:** `venv\Scripts\activate`

4.  **Launch the servers:**
    ```bash
    python start_servers.py
    ```
    This will start the web interface (usually at `http://127.0.0.1:5000`) and the remote API server.

## 🌐 Web Dashboard

After launching the servers, open your web browser and navigate to `http://127.0.0.1:5000` to access the modern web interface.

## ✨ Key Features

News02 offers a rich set of features designed for a professional news digest experience:

### 🤖 Multi-Provider LLM Support with Smart Rate Limiting
-   Integrates with **Ollama** (for local inference), **OpenAI-Compatible** APIs (vLLM, LocalAI), and **Google Gemini** (cloud-based).
-   **Automatic Rate Management** prevents `429` errors with intelligent delays, optimizing usage for free tiers.

### 🌐 Comprehensive Web Interface (WebGUI)
-   **Real-time Dashboard**: Monitor digest generation progress and system statistics.
-   **News Lounge**: A comfortable interface for viewing and listening to generated digests.
-   **Feed Management**: Easily add, test, and organize RSS feeds with built-in reliability testing.
-   **Settings Panel**: Configure LLM providers, API keys, and other system preferences with live connection testing.
-   **Mobile Responsive**: Optimized for seamless use across phones, tablets, and desktops.

### ⚙️ Automated Job Scheduling
-   **Jobs Page**: Schedule automated digest generations based on RSS profiles.
-   **Flexible Scheduling**: Set daily, weekday, weekend, or one-time jobs with precise timing.
-   **Customizable Output**: Define specific LLM models and article limits for each scheduled job.
-   **Queue Management**: Ensures efficient processing with conflict prevention and real-time status updates.

### 💾 Robust Database Management
-   **SQLite Storage**: Persistently stores articles, summaries, and generated digests.
-   **Real-time Analytics**: Provides insights into feed performance and processing statistics.
-   **Smart Deduplication**: Avoids reprocessing duplicate articles.
-   **History Tracking**: Browse and access past digests and summaries.
-   **Database Tools**: Options to reset, clean up, or wipe the database.

### 🎵 Audio Generation (TTS)
-   **Text-to-Speech**: Generates high-quality audio narration using multiple voice options via Microsoft Edge TTS.
-   **News Anchor Style**: Formats broadcasts professionally with transitions.
-   **Integrated Audio Player**: Play generated content directly within the web interface.
-   **Download Options**: Save MP3 audio files locally.

### 📋 Complete Source Transparency
-   **Detailed Article Sources**: Tracks individual articles with titles and original URLs.
-   **Source Statistics**: Provides counts like "X articles from Y sources."
-   **Clickable Sources**: Direct links to original articles for verification.
-   **Copy Functionality**: Easily copy URLs for sharing.

### 🔍 Advanced RSS Feed Discovery
-   **300+ Curated Feeds**: Automatically cloned from the `awesome-rss-feeds` repository.
-   **Smart Search & Filters**: Find feeds by topic, keyword, category, or country (e.g., English-only, US, UK).
-   **One-Click Adding**: Test and add feeds directly to your collection.
-   **Live Feed Testing**: Verify feed functionality before adding.

## 🔧 Configuration

### Environment Variables (.env) (Also handled in the WebGUI via Settings page)
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

## 📁 Project Structure

```
News02/
├── 🌐 Web Interface
│   ├── web_app.py              # Enhanced Flask application
│   ├── run_web.py              # Web launcher
│   ├── templates/              # HTML templates
│   │   ├── lounge.html         # News consumption interface
│   │   ├── dashboard.html      # Real-time monitoring
│   │   ├── feeds.html          # Feed discovery & management
│   │   └── settings.html       # Configuration management
│   └── static/                 # Modern CSS, JS, images
├── 🤖 Enhanced Core System
│   ├── news_digest_enhanced.py # broadcast generation
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
└── 🛠️ Tools
    ├── auto_setup.py          # Intelligent setup script
    ├── quick_setup.bat/.sh    # Platform launchers
    └── news_cli.py            # Enhanced command-line utilities
```

## 📚 Documentation

Here are detailed guides and examples for advanced usage and deployment:

- **[🚀 Deployment Guide](documents/DEPLOYMENT_GUIDE.md)**: Comprehensive instructions for deploying News02 in a production environment, including Nginx, Docker, and SSL/TLS configurations. It covers single instance and separate service architectures.
- **[⚙️ Jobs System](documents/JOBS_SYSTEM_README.md)**: Documentation for setting up and managing automated, scheduled RSS digest generation. Learn how to create RSS profiles, schedule jobs with flexible recurrence, and monitor job execution.
- **[☁️ Proxy Deployment](documents/PROXY_DEPLOYMENT.md)**: A guide for deploying News02 behind a proxy server like Cloudflare or Nginx, simplifying SSL and domain management.
- **[📡 Remote API](documents/REMOTE_API_README.md)**: Detailed documentation for the News02 Remote Digest API, enabling external applications to securely access generated digests, server statistics, and RSS profiles. Includes API key authentication, rate limiting, and usage examples.
- **[CLI Usage Examples](documents/usage_examples.md)**: Provides various command-line examples for launching News02 servers with different configurations, useful for development, testing, and public demos.

## 🎯 Core Workflow

Here's the typical workflow for using News02:

1.  **Setup**: Follow the "Quick Start" guide to get the system installed and running.
2.  **Configure**: Access the web dashboard's "Settings" page to configure your LLM providers and other preferences.
3.  **Discover & Manage Feeds**: Use the "Feeds" page to browse over 300 curated RSS feeds, search for new ones, and add them to your collection.
4.  **Generate Digests**: Manually generate digests from your selected feeds, or schedule automated jobs via the "Jobs" page.
5.  **Consume Content**: Enjoy your personalized news digests in the "News Lounge" with integrated audio playback and full source transparency.
6.  **Monitor & Maintain**: Use the "Dashboard" for real-time monitoring and the "History" page for past digests and analytics.

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
-   **Python 3.8+** with pip
-   **2GB RAM** for basic operation
-   **Internet connection** for RSS feeds and LLM APIs
-   **Modern web browser** for the web dashboard

### Recommended
-   **Python 3.10+** for optimal performance
-   **4GB+ RAM** for faster processing and larger models
-   **SSD storage** for improved database performance
-   **Chrome/Firefox** for the best web experience

### Common Issues
-   **Port conflicts**: If the web interface or API server fails to start, try changing `WEB_PORT` or `REMOTE_API_PORT` in your `.env` file.
-   **Import errors**: Ensure your Python virtual environment is activated before running scripts.
-   **LLM failures**: Verify your LLM provider connections and API keys in the web dashboard's "Settings" tab.
-   **Feed errors**: Use the "Feeds" tab in the web interface to validate RSS feed URLs and check their health.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **awesome-rss-feeds** - Curated RSS feed collection by plenaryapp
- **Ollama** - Local LLM inference platform
- **Google** - Gemini AI integration
- **Microsoft** - Edge TTS service
-   **Bootstrap**: Web interface framework for responsive design.

---

**🚀 Ready to get started?** Follow the "Quick Start" guide above to deploy your AI news digest system!
