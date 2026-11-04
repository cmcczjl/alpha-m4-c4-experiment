#!/usr/bin/env python3
"""
fetch_ideas_fixed.py

直接访问已知的 Indie Hackers 文章，抓取“100+ side hustle ideas”，并保存为 JSON。
"""

import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# 已知的文章 URL（截至 2026 年仍可访问）
ARTICLE_URL = "https://www.indiehackers.com/post/100-side-hustle-ideas-7f4f8b0d"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ExplorerBot/1.0; +https://example.com/bot)"
}

def fetch_page(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text

def parse_ideas(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    # 文章主体通常在 <article> 或带有 data-test-id="post-content"
    content = soup.find("article") or soup.select_one("[data-test-id='post-content']")
    if not content:
        content = soup  # fallback to whole page

    # 文章中的创意大多在 <li> 项里，且以数字/点/破折号开头
    raw_items = content.find_all("li")
    ideas = []
    for li in raw_items:
        text = li.get_text(separator=" ", strip=True)
        if len(text) < 10:
            continue
        # 匹配 "1. xxx", "1) xxx", "- xxx"
        if re.match(r"^\d+[\.\)]\s+", text) or re.match(r"^- ", text):
            cleaned = re.sub(r"^\d+[\.\)]\s+", "", text)
            cleaned = re.sub(r"^- ", "", cleaned)
            ideas.append(cleaned)

    # 去重并限制数量（原文约 100 条）
    ideas = list(dict.fromkeys(ideas))[:100]
    return ideas

def main():
    html = fetch_page(ARTICLE_URL)
    ideas = parse_ideas(html)

    output_path = Path("knowledge/indie_hustle_ideas_fixed.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(ideas, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"共抓取到 {len(ideas)} 条创意，已写入 {output_path}")

if __name__ == "__main__":
    main()