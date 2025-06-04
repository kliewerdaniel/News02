# 📰 AI News Digest Generator

This Python script automatically fetches news articles from RSS feeds, summarizes them using a local LLM (via Ollama), writes a coherent broadcast-style script, and generates a text-to-speech (TTS) audio file of the broadcast.

## ✨ Features

- Pulls articles from any RSS feed (configurable via `feeds.yaml`)
- Summarizes news using a local LLM (Ollama)
- Generates a flowing, anchor-style news script
- Converts the script into an MP3 audio broadcast using Microsoft Edge TTS
- Saves both text and audio versions with timestamped filenames

---

## 🔧 Configurable Models

You can easily modify which models or voices to use by changing these variables at the top of the script:

```python
# === CONFIGURABLE MODELS ===
SUMMARY_MODEL = 'mistral:latest'            # For summarizing articles
BROADCAST_MODEL = 'mistral-small:24b-instruct-2501-q8_0'  # For combining summaries into a narrative
TTS_VOICE = "en-US-GuyNeural"               # Microsoft Edge TTS voice
# ===========================
```

---

## 📦 Installation

1. **Clone this repository:**
   ```bash
   git clone https://github.com/kliewerdaniel/news02.git
   cd news02
   ```

2. **Install dependencies:**
   Make sure you have Python 3.8+ and install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Ollama (if not already):**
   Follow setup instructions at https://ollama.com

---

## 📄 feeds.yaml Example

Create a file called `feeds.yaml` in the project root:

```yaml
feeds:
  - https://rss.nytimes.com/services/xml/rss/nyt/World.xml
  - https://feeds.bbci.co.uk/news/rss.xml
```

---

## 🚀 Running the Script

```bash
python your_script_name.py
```

The script will:
- Fetch one article per feed
- Summarize each
- Generate a full news digest
- Save the digest as `digest_YYYY-MM-DD_HH-MM-SS.md`
- Save an audio file as `digest_YYYY-MM-DD_HH-MM-SS.mp3`

---

## 🗣️ Voice Options

You can change the voice used for TTS by editing the `TTS_VOICE` variable. Supported voices include:
- `en-US-GuyNeural` (default, male)
- `en-US-JennyNeural` (female)
- `en-GB-RyanNeural` (UK male)
- `en-IN-PrabhatNeural` (Indian English male)

See [Edge TTS Voice List](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support) for more.

---

## 🧠 Customization Tips

- Adjust `max_articles` in `fetch_articles()` to increase the number of articles per feed
- Modify the `summarize_with_ollama()` and `generate_broadcast()` prompts for a different tone or depth
- Swap `SUMMARY_MODEL` or `BROADCAST_MODEL` to use other Ollama-supported models like `llama3`, `gemma`, etc.

---

## 📁 Output

- Markdown news summary file
- Matching MP3 file with TTS narration

Files are saved in the same directory by default. You can change `output_dir` in `save_digest()`.

---

## 🔒 License

MIT License