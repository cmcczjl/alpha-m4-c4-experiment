#!/usr/bin/env python3
"""
Simple news‑digest workflow:
1. Pull a few RSS feeds.
2. Download each article page.
3. Strip HTML → plain text.
4. Produce a very short summary (first 3 sentences).
5. Write a timestamped text file per article into data/output/.
"""

import os
import re
import sys
import time
import hashlib
from datetime import datetime
from urllib.parse import urlparse, quote_plus

try:
    import feedparser
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    print("Missing dependencies. Install with: pip3 install feedparser requests beautifulsoup4", file=sys.stderr)
    sys.exit(1)


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
RSS_FEEDS = [
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.reddit.com/r/worldnews/.rss"
]

OUTPUT_DIR = "data/output"
MAX_ARTICLES = 5          # how many articles to process per run
SUMMARY_SENTENCES = 3    # number of sentences in the summary


# ----------------------------------------------------------------------
def slugify(text: str) -> str:
    """Create a filesystem‑friendly slug from a title."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:50]  # limit length


def fetch_article(url: str) -> str:
    """Download an article and return its cleaned text."""
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except Exception as exc:
        print(f"Failed to fetch {url}: {exc}", file=sys.stderr)
        return ""

    soup = BeautifulSoup(resp.content, "html.parser")

    # Remove scripts / styles
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # Get visible text
    text = soup.get_text(separator=" ", strip=True)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text


def summarize(text: str, n_sentences: int = SUMMARY_SENTENCES) -> str:
    """Very naive summarizer: return the first n_sentences."""
    # Split on punctuation that usually ends a sentence
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(sentences[:n_sentences]).strip()


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def write_summary(title: str, url: str, summary: str):
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    slug = slugify(title) or hashlib.sha1(url.encode()).hexdigest()[:8]
    filename = f"{timestamp}_{slug}.txt"
    path = os.path.join(OUTPUT_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Title: {title}\n")
        f.write(f"URL: {url}\n\n")
        f.write(summary + "\n")
    print(f"✔️  Written summary to {path}")


def main():
    ensure_output_dir()
    processed = 0

    for feed_url in RSS_FEEDS:
        if processed >= MAX_ARTICLES:
            break
        print(f"🔎 Fetching feed: {feed_url}")
        feed = feedparser.parse(feed_url)

        for entry in feed.entries:
            if processed >= MAX_ARTICLES:
                break
            title = entry.get("title", "No Title")
            link = entry.get("link")
            if not link:
                continue

            print(f"📄 Processing article: {title}")
            article_text = fetch_article(link)
            if not article_text:
                continue

            summary = summarize(article_text)
            if not summary:
                continue

            write_summary(title, link, summary)
            processed += 1

    if processed == 0:
        print("⚠️  No articles processed.", file=sys.stderr)
    else:
        print(f"✅ Finished. Produced {processed} summary file(s).")


if __name__ == "__main__":
    main()