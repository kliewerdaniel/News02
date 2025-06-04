# === CONFIGURABLE MODELS ===
SUMMARY_MODEL = 'mistral:latest'
BROADCAST_MODEL = 'mistral-small:24b-instruct-2501-q8_0'
TTS_VOICE = "en-US-GuyNeural"  # Change voice if desired
# ===========================

import os
import yaml
import feedparser
from newspaper import Article
from datetime import datetime
import asyncio
import edge_tts
import ollama
from tqdm import tqdm  # Progress bar

# Load feed URLs from YAML configuration
def load_feeds(config_path='feeds.yaml'):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config.get('feeds', [])

# Fetch and parse articles from RSS feeds
def fetch_articles(feed_urls, max_articles=1):
    articles = []
    print("Fetching and parsing RSS feeds...\n")
    for url in tqdm(feed_urls, desc="Scraping feeds", unit="feed"):
        feed = feedparser.parse(url)
        for entry in feed.entries[:max_articles]:
            articles.append({
                'title': entry.title,
                'link': entry.link,
                'published': entry.get('published', 'N/A')
            })
    return articles

# Use Ollama to summarize text
def summarize_with_ollama(text, model=SUMMARY_MODEL):
    prompt = (
        "Summarize the following news article in 3-5 sentences, focusing on the key facts, context, "
        "and implications. Avoid speculation and opinion.\n\n"
        f"{text}\n\nSummary:"
    )
    response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
    return response['message']['content']

# Extract and summarize article content using Ollama
def summarize_articles(articles, model=SUMMARY_MODEL):
    summaries = []
    print("\nSummarizing articles...\n")
    for article in tqdm(articles, desc="Summarizing", unit="article"):
        try:
            news_article = Article(article['link'])
            news_article.download()
            news_article.parse()
            text = news_article.text[:2000]
            summary = summarize_with_ollama(text, model=model)
            summaries.append({
                'title': article['title'],
                'link': article['link'],
                'published': article['published'],
                'summary': summary
            })
        except Exception as e:
            print(f"Error processing article: {article['link']}\n{e}")
    return summaries

# Use Ollama to generate a cohesive news broadcast from all summaries
def generate_broadcast(summaries, model=BROADCAST_MODEL):
    joined_summaries = "\n\n".join(
        f"Title: {s['title']}\nSummary: {s['summary']}" for s in summaries
    )
    prompt = (
        "You are a professional news anchor. Create a coherent news broadcast script based on the following article summaries. "
        "Weave them together into a flowing narrative, grouping related topics and keeping it informative and neutral:\n\n"
        f"{joined_summaries}\n\nBroadcast:"
    )
    response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
    return response['message']['content']

# Save full broadcast with timestamped filename
def save_digest(digest_text, output_dir='.'):
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = os.path.join(output_dir, f'digest_{timestamp}.md')
    with open(filename, 'w') as file:
        file.write(digest_text)
    return filename  # return path for TTS to use

# Convert broadcast to speech with timestamped filename
async def text_to_speech(text, output_path, voice=TTS_VOICE):
    communicate = edge_tts.Communicate(text, voice=voice)
    await communicate.save(output_path)

# Main workflow
def main():
    feed_urls = load_feeds()
    articles = fetch_articles(feed_urls, max_articles=1)
    summaries = summarize_articles(articles)
    broadcast = generate_broadcast(summaries)

    # Save digest and get timestamped filename
    digest_path = save_digest(broadcast)

    # Create matching timestamped mp3 path
    mp3_path = digest_path.replace('.md', '.mp3')
    asyncio.run(text_to_speech(broadcast, output_path=mp3_path))

if __name__ == "__main__":
    main()