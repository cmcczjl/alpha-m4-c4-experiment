#!/usr/bin/env python3
import os
import feedparser
import requests
from datetime import datetime
import re

# 配置
RSS_FEEDS = [
    "https://news.ycombinator.com/rss",
    "https://hnrss.org/frontpage",
    "https://www.reddit.com/r/technology/.rss"
]
OUTPUT_DIR = "data/output"
MIN_SUMMARIES = 3

def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_and_digest():
    summaries_count = 0
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for url in RSS_FEEDS:
        if summaries_count >= MIN_SUMMARIES:
            break
        try:
            print(f"Fetching {url}...")
            feed = feedparser.parse(url)
            if not feed.entries:
                continue
                
            for entry in feed.entries[:5]: # 每个源取前5条
                if summaries_count >= MIN_SUMMARIES:
                    break
                    
                title = entry.get('title', 'No Title')
                link = entry.get('link', '#')
                summary_text = entry.get('summary', 'No content available.')
                # 简单清洗 HTML 标签
                summary_text = re.sub('<[^<]+?>', '', summary_text)[:300] + "..."
                
                filename = f"digest_{timestamp}_{summaries_count}.txt"
                filepath = os.path.join(OUTPUT_DIR, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Title: {title}\n")
                    f.write(f"Link: {link}\n")
                    f.write(f"Date: {datetime.now().isoformat()}\n")
                    f.write("-" * 20 + "\n")
                    f.write(f"Summary: {summary_text}\n")
                
                print(f"Generated: {filepath}")
                summaries_count += 1
        except Exception as e:
            print(f"Error processing {url}: {e}")
            continue
            
    return summaries_count

if __name__ == "__main__":
    ensure_dirs()
    count = fetch_and_digest()
    print(f"Successfully generated {count} summaries.")
    if count < MIN_SUMMARIES:
        exit(1)