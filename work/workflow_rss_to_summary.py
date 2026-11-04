#!/usr/bin/env python3
import os
import sys
import subprocess
import datetime
import json
from urllib.request import urlopen

# Ensure feedparser is available
try:
    import feedparser
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "feedparser"])
    import feedparser

OUTPUT_DIR = os.path.join("data", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Hard‑coded RSS feed list (feel free to extend)
RSS_FEEDS = [
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
]

def fetch_feed(url):
    """Return parsed feed or None on failure."""
    try:
        # feedparser can handle URLs directly
        return feedparser.parse(url)
    except Exception as e:
        print(f"Failed to fetch {url}: {e}", file=sys.stderr)
        return None

def summarise_entry(entry):
    """Create a simple summary string for an RSS entry."""
    title = entry.get("title", "No Title")
    link = entry.get("link", "")
    published = entry.get("published", "No Date")
    summary = entry.get("summary", "")
    # Very lightweight “summary” – title + first 200 chars of description
    short_desc = (summary[:200] + "...") if len(summary) > 200 else summary
    return f"Title: {title}\nPublished: {published}\nLink: {link}\n\n{short_desc}\n"

def write_summary(content, idx):
    """Write content to a timestamped file."""
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"summary_{timestamp}_{idx}.txt"
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path

def main():
    count = 0
    for feed_url in RSS_FEEDS:
        feed = fetch_feed(feed_url)
        if not feed or feed.bozo:
            continue
        for entry in feed.entries[:5]:  # limit to a few entries per feed
            summary = summarise_entry(entry)
            write_summary(summary, count)
            count += 1
            if count >= 3:  # we need at least three files
                break
        if count >= 3:
            break
    if count == 0:
        print("No entries were processed.", file=sys.stderr)
    else:
        print(f"Generated {count} summary file(s) in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()