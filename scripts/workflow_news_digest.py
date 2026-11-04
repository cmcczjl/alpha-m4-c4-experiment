#!/usr/bin/env python3
import json
import os
import sys
import subprocess
from datetime import datetime

# Ensure feedparser is available
try:
    import feedparser
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "feedparser"])
    import feedparser

def fetch_and_summarize():
    feed_url = "https://news.google.com/rss"
    parsed = feedparser.parse(feed_url)

    # Prepare output directory
    out_dir = os.path.join("data", "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "news_digest.json")

    summaries = []
    for entry in parsed.entries[:5]:
        summaries.append({
            "title": entry.get("title", ""),
            "published": entry.get("published", ""),
            "summary": entry.get("summary", "")[:200]  # truncate for brevity
        })

    # Write JSON output
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)

    print(f"News digest written to {out_path}")

if __name__ == "__main__":
    fetch_and_summarize()