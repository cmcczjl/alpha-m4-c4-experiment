#!/usr/bin/env python3
"""
fetch_ideas.py

从 Indie Hackers 的 “100+ side hustle ideas” 文章抓取创意列表并保存为 JSON。
"""

import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# 1. 先在 DuckDuckGo 上搜索目标文章，取第一个结果的链接
SEARCH_URL = "https://duckduckgo.com/html/"
params = {"q": "Indie Hackers 100 side hustle ideas"}
headers = {
    "User-Agent": "Mozilla/5.0 (compatible; ExplorerBot/1.0; +https://example.com/bot)"
}
resp = requests.get(SEARCH_URL, params=params, headers=headers, timeout=15)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")
first_result = soup.select_one("a.result__a")
if not first_result:
    print("未找到搜索结果", file=sys.stderr)
    sys.exit(1)

article_url = first_result["href"]
print(f"目标文章 URL: {article_url}")

# 2. 抓取文章内容
article_resp = requests.get(article_url, headers=headers, timeout=15)
article_resp.raise_for_status()
article_soup = BeautifulSoup(article_resp.text, "html.parser")

# 3. 页面中创意多以 <li> 项目出现，且包含数字或 “- ” 前缀
raw_items = article_soup.find_all("li")
ideas = []
for li in raw_items:
    text = li.get_text(separator=" ", strip=True)
    # 简单过滤掉明显不是创意的项目（比如导航、评论等）
    if len(text) < 10:
        continue
    # 只保留以数字/点/破折号开头的行
    if re.match(r"^\d+[\.\)]\s+", text) or re.match(r"^- ", text):
        # 去掉前导编号
        cleaned = re.sub(r"^\d+[\.\)]\s+", "", text)
        cleaned = re.sub(r"^- ", "", cleaned)
        ideas.append(cleaned)

# 去重并截断到 100 条（文章原本约 100 条）
ideas = list(dict.fromkeys(ideas))[:100]

output_path = Path("knowledge/indie_hustle_ideas.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(ideas, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"共抓取到 {len(ideas)} 条创意，已写入 {output_path}")