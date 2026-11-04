#!/usr/bin/env python3
"""
Simple RSS digest: fetch RSS, write 3 titles with timestamps to data/output/news_digest.txt.
"""
import os
import time
import requests
import xml.etree.ElementTree as ET

# Configuration
RSS_URL = "https://news.un.org/feed/subscribe/en/news/all/rss.xml"
OUT_DIR = "data/output"
OUT_FILE = os.path.join(OUT_DIR, "news_digest.txt")

def fetch_titles(limit=3):
    """Fetch the latest RSS items and return a list of (title, pubDate)."""
    resp = requests.get(RSS_URL, timeout=10)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    items = root.findall('.//item')[:limit]
    titles = []
    for item in items:
        title_el = item.find('title')
        date_el = item.find('pubDate')
        if title_el is not None:
            title = title_el.text.strip()
        else:
            title = "No title"
        if date_el is not None:
            pub_date = date_el.text.strip()
        else:
            pub_date = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        titles.append((title, pub_date))
    return titles

def write_digest(titles):
    """Append titles with timestamps to the output file."""
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_FILE, "a", encoding="utf-8") as f:
        for title, pub_date in titles:
            line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {pub_date} | {title}\n"
            f.write(line)
    print(f"Wrote {len(titles)} entries to {OUT_FILE}")

def main():
    titles = fetch_titles()
    write_digest(titles)

if __name__ == "__main__":
    main()