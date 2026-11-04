#!/usr/bin/env python3
import urllib.request, re, os
from urllib.parse import unquote, urlparse, parse_qs

query = 'upwork workflow automation'
url = f'https://html.duckduckgo.com/html/?q={query.replace(" ", "+")}'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
except Exception as e:
    html = ""
    print(f"Error fetching: {e}")

# 匹配 DuckDuckGo 搜索结果
items = re.findall(r'<a rel="nofollow" class="result__a" href="(.*?)".*?>(.*?)</a>', html, re.S)
lines = []
for link, title in items[:3]:
    clean_title = re.sub(r'<.*?>', '', title).strip()
    # 解析 DuckDuckGo 的重定向链接获取真实 URL
    if 'uddg=' in link:
        parsed = urlparse(link)
        qs = parse_qs(parsed.query)
        real_link = unquote(qs.get('uddg', [link])[0])
    else:
        real_link = link
    lines.append(f"- Title: {clean_title}\n  URL: {real_link}\n  Description: (自动抓取未实现)\n")

content = "\n".join(lines) if lines else "No results found or blocked by captcha."

os.makedirs('data', exist_ok=True)
with open('data/search_results.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("Search results saved to data/search_results.md")
print("---")
print(content)