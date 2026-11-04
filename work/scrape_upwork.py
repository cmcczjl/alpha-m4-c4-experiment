#!/usr/bin/env python3
import requests
import re
import os
from datetime import datetime

def scrape_market_data():
    # 使用 DuckDuckGo HTML 接口搜索 Upwork 关于 n8n 和 Make.com 的外包需求
    # 模拟浏览器 Header
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    
    queries = [
        'site:upwork.com "n8n" automation job',
        'site:upwork.com "Make.com" automation job',
        'site:fiverr.com "n8n" workflow'
    ]
    
    results = []
    
    for query in queries:
        # 使用 DuckDuckGo 的 HTML 视图接口，避免复杂的 JS 渲染
        ddg_url = f"https://html.duckduckgo.com/html/?q={query}"
        try:
            response = requests.get(ddg_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 简单的正则解析：匹配标题、链接和描述摘要
            # HTML 结构：<a class="result__a" href="...">标题</a> <div class="result__snippet">描述</div>
            blocks = re.findall(r'<div class="result__body">.*?<a class="result__a" href="(.*?)">(.*?)</a>.*?<div class="result__snippet">(.*?)</div>', response.text, re.S)
            
            for link, title, snippet in blocks:
                # 过滤掉不相关的搜索结果（如帮助文档）
                if "help" in link or "faq" in link:
                    continue
                
                results.append({
                    "title": title.strip(),
                    "url": link,
                    "description": snippet.strip().replace('<br>', '\n')
                })
        except Exception as e:
            print(f"Error scraping {query}: {e}")

    # 准备写入目录
    output_dir = "data/market_research"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, "requirements.md")

    # 写入文件
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# Market Research: n8n/Make Automation Requirements\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        if not results:
            f.write("## No specific requirements found. Try broadening the query.\n")
        else:
            for i, res in enumerate(results, 1):
                f.write(f"### Requirement {i}: {res['title']}\n")
                f.write(f"- **Source**: [{res['url']}]({res['url']})\n")
                f.write(f"- **Description**:\n  {res['description']}\n\n")
                
    print(f"Successfully saved {len(results)} requirements to {file_path}")

if __name__ == "__main__":
    scrape_market_data()