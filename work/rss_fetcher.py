#!/usr/bin/env python3
import feedparser
import json
import datetime
import sys

def fetch_and_summarize(rss_url):
    """
    解析 RSS 源并获取前 5 条条目的标题和链接。
    """
    try:
        feed = feedparser.parse(rss_url)
        if feed.bozo:
            return json.dumps({"error": f"Feed parsing error: {feed.bozo_exception}"})
            
        summaries = []
        for entry in feed.entries[:5]:
            title = entry.get('title', 'No Title')
            link = entry.get('link', 'No Link')
            # 尝试获取发布时间，若无则使用当前 UTC 时间
            published = entry.get('published', datetime.datetime.utcnow().isoformat())
            summaries.append({
                "title": title,
                "link": link,
                "published": published
            })
        return json.dumps(summaries, indent=4, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    # 默认使用一个公共 RSS 源进行演示（例如 Python 官方新闻）
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.python.org/static/community_logos/python-logo.png" 
    # 注意：上面的 URL 只是占位，实际运行会尝试解析，如果 URL 无效会报错。
    # 为了演示可运行，我们尝试使用一个真实的 RSS 地址
    if len(sys.argv) < 2:
        target_url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
    else:
        target_url = sys.argv[1]
        
    print(fetch_and_summarize(target_url))