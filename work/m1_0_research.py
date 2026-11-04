#!/usr/bin/env python3
"""M1-0: 真实市场需求调研（固定可达数据源，不依赖 DDG 动态搜索）"""
import urllib.request, re, os
from datetime import datetime, timezone

UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) Firefox/115.0'}

SOURCES = [
    ('upwatcher AI 自由职业市场', 'https://www.upwatcher.io/market/ai/'),
    ('digiko Upwork/Fiverr AI 报酬报告', 'https://digiko.io/money/ai-freelance-pay-in-2026-what-upwork-and-fiverr-actually-report'),
    ('betonai n8n/Make 自动化', 'https://betonai.net/'),
]

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode('utf-8', errors='ignore')

def extract_signals(html, limit=8):
    """从 HTML 提取标题 + 含金额/岗位关键词的文本片段"""
    text = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', html, flags=re.S)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    # 找含 $ 金额或岗位关键词的句子
    frags = re.split(r'(?<=[.!?])\s+', text)
    keep = [f.strip() for f in frags if re.search(r'\$\d|\d+\s*/\s*hr|per hour|freelance|workflow|automation|RAG|n8n|Upwork|Fiverr|rate|price|budget', f, re.I) and 30 < len(f.strip()) < 300]
    seen, out = set(), []
    for f in keep:
        k = f[:60]
        if k not in seen:
            seen.add(k)
            out.append(f)
        if len(out) >= limit:
            break
    return out

def main():
    out_dir = 'data/market_research'
    os.makedirs(out_dir, exist_ok=True)
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = [f'# Market Research: n8n/Make 自动化工作流真实需求', f'Generated: {now}', '']
    ok = 0
    for i, (name, url) in enumerate(SOURCES, 1):
        lines.append(f'## 需求源 {i}: {name}')
        lines.append(f'来源URL: {url}')
        try:
            html = fetch(url)
            signals = extract_signals(html)
            if signals:
                ok += 1
                for s in signals:
                    lines.append(f'- {s}')
            else:
                lines.append('- (抓取成功但未提取到有效信号)')
        except Exception as e:
            lines.append(f'- 抓取失败: {e}')
        lines.append('')
    with open(f'{out_dir}/requirements.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'Saved {ok}/{len(SOURCES)} sources to {out_dir}/requirements.md')
    # 验收：≥3 条带来源 URL
    content = open(f'{out_dir}/requirements.md').read()
    urls = re.findall(r'来源URL:\s*(\S+)', content)
    if ok >= 3 and len(urls) >= 3:
        print('M1-0 CHECK PASSED: ≥3 sources with URLs')
    else:
        print(f'M1-0 CHECK FAILED: only {ok} ok sources')

if __name__ == '__main__':
    main()
