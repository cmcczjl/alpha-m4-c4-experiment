#!/usr/bin/env python3
import feedparser
import datetime
import os
import json
import argparse

def fetch_and_summarize(url, limit=3, output_dir="data/output"):
    """从 RSS feed 抓取新闻并生成摘要"""
    os.makedirs(output_dir, exist_ok=True)
    
    feed = feedparser.parse(url)
    if not feed.entries:
        print(f"无法获取 feed: {url}")
        return []
    
    summaries = []
    for entry in feed.entries[:limit]:
        title = entry.get('title', 'No Title')
        summary = entry.get('summary', '') or entry.get('description', '')
        short = summary[:200].replace('\n', ' ').strip()
        ts = datetime.datetime.now().isoformat(timespec='seconds')
        summaries.append({
            "timestamp": ts,
            "title": title,
            "summary": short
        })
    
    # 保存结果
    safe_name = url.replace('://', '_').replace('/', '_')[:50]
    output_file = os.path.join(output_dir, f"{safe_name}_digest.json")
    
    result = {
        "url": url,
        "fetched_at": datetime.datetime.now().isoformat(timespec='seconds'),
        "entries": summaries
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"已保存 {len(summaries)} 条摘要到: {output_file}")
    return summaries

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RSS 新闻摘要工具")
    parser.add_argument("url", help="RSS feed URL")
    parser.add_argument("-n", "--limit", type=int, default=3, help="抓取数量")
    args = parser.parse_args()
    
    fetch_and_summarize(args.url, args.limit)