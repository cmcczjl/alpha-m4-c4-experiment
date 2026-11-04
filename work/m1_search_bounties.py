#!/usr/bin/env python3
"""
M1-0: Search GitHub issues with bounty/need-help labels for 'AI agent automation'.
Extract real paid requirements & pricing → data/market_research/requirements.md
"""
import os, json, re, urllib.request, urllib.parse
from datetime import datetime

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
OUTPUT_DIR = 'data/market_research'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'requirements.md')

def gh_search_issues(query, per_page=30, max_pages=2):
    """Search GitHub issues via REST API with pagination."""
    encoded = urllib.parse.quote(query)
    results = []
    for page in range(1, max_pages + 1):
        url = f'https://api.github.com/search/issues?q={encoded}&sort=created&order=desc&per_page={per_page}&page={page}'
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/vnd.github.v3+json')
        req.add_header('User-Agent', 'market-research-bot')
        if GITHUB_TOKEN:
            req.add_header('Authorization', f'token {GITHUB_TOKEN}')
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                items = data.get('items', [])
                results.extend(items)
                if len(items) < per_page:
                    break
        except Exception as e:
            print(f'  [WARN] page {page} failed: {e}')
            break
    return results

def extract_amount(text):
    """Extract dollar/ETH/USDC amounts from text."""
    if not text:
        return None
    patterns = [
        r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|USDC)',
        r'(\d+(?:\.\d+)?)\s*ETH',
        r'[Bb]ounty[:\s]*\$?\s*(\d{1,3}(?:,\d{3})*)',
        r'[Rr]eward[:\s]*\$?\s*(\d{1,3}(?:,\d{3})*)',
        r'[Pp]rize[:\s]*\$?\s*(\d{1,3}(?:,\d{3})*)',
        r'[Pp]ay(?:ment)?[:\s]*\$?\s*(\d{1,3}(?:,\d{3})*)',
    ]
    amounts = []
    for p in patterns:
        for m in re.findall(p, text):
            try:
                val = float(m.replace(',', ''))
                if 1 <= val <= 1_000_000:
                    amounts.append(val)
            except ValueError:
                pass
    return max(amounts) if amounts else None

def search_bounties():
    """Run multiple targeted bounty searches and deduplicate."""
    queries = [
        'AI agent automation label:bounty',
        'AI agent automation label:need-help',
        'AI agent label:bounty',
        'automation agent label:bounty',
        'LLM agent label:bounty',
        'AI agent label:"help wanted"',
        'AI agent automation label:"help wanted"',
        'agent automation label:need-help',
        'AI agent label:bounties',
        'autonomous agent label:bounty',
    ]
    seen_ids = set()
    all_items = []
    for q in queries:
        print(f'[SEARCH] {q}')
        items = gh_search_issues(q, per_page=30, max_pages=2)
        new = 0
        for it in items:
            if it['id'] not in seen_ids:
                seen_ids.add(it['id'])
                all_items.append(it)
                new += 1
        print(f'  → {len(items)} results, {new} new (total: {len(all_items)})')
    return all_items

def format_entry(item, idx):
    title = item.get('title', 'N/A')
    html_url = item.get('html_url', '')
    state = item.get('state', 'unknown')
    created = item.get('created_at', '')
    repo_url = item.get('repository_url', '')
    repo_full = repo_url.replace('https://api.github.com/repos/', '') if repo_url else 'unknown'
    body = item.get('body') or ''
    body_clean = re.sub(r'<[^>]+>', '', body)
    body_preview = body_clean[:800].replace('\n', ' ').strip()
    if not body_preview:
        body_preview = '(No description provided)'
    labels = [l['name'] for l in item.get('labels', [])]
    full_text = f'{title} {body}'
    amount = extract_amount(full_text)
    amount_str = f'${amount:,.2f}' if amount else 'Not explicitly stated'
    entry = f"""## Bounty Entry #{idx}

- **Title**: {title}
- **Repository**: {repo_full}
- **Issue URL**: {html_url}
- **State**: {state}
- **Bounty Amount**: {amount_str}
- **Labels**: {', '.join(labels) if labels else '(none)'}
- **Created**: {created}
- **Requirement Description**: {body_preview}

---
"""
    return entry, amount

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    bounties = search_bounties()
    print(f'\n[INFO] Total unique bounty issues: {len(bounties)}')

    if not bounties:
        print('[WARN] No bounties found — writing minimal file')
        with open(OUTPUT_FILE, 'w') as f:
            f.write('# Market Research: AI Agent Automation Bounties\n\n')
            f.write(f'> Generated: {datetime.utcnow().isoformat()}Z\n')
            f.write('> Status: No bounty issues found in this search run.\n\n')
        return

    md = []
    md.append('# Market Research: AI Agent Automation — Bounty Requirements')
    md.append('')
    md.append(f'> Generated: {datetime.utcnow().isoformat()}Z')
    md.append('> Source: GitHub Issues (bounty / need-help / help-wanted labels)')
    md.append(f'> Total bounty entries: {len(bounties)}')
    md.append('')
    md.append('---')
    md.append('')

    amounts = []
    for i, item in enumerate(bounties, 1):
        entry, amt = format_entry(item, i)
        md.append(entry)
        if amt:
            amounts.append(amt)

    md.append('## Pricing Summary')
    md.append('')
    md.append(f'- Total bounty issues: {len(bounties)}')
    md.append(f'- Issues with explicit pricing: {len(amounts)}')
    if amounts:
        md.append(f'- Price range: ${min(amounts):.2f} – ${max(amounts):.2f}')
        md.append(f'- Average: ${sum(amounts)/len(amounts):.2f}')
        md.append(f'- Median: ${sorted(amounts)[len(amounts)//2]:.2f}')
    else:
        md.append('- No explicit dollar amounts found in issue text')
    md.append('')

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

    print(f'[OK] Written to {OUTPUT_FILE}')
    print(f'[OK] Bounty entries: {len(bounties)}')
    print(f'[OK] Priced entries: {len(amounts)}')
    # Quick preview
    for i, item in enumerate(bounties[:5]):
        t = item.get('title', 'N/A')
        ft = f"{item.get('title','')} {item.get('body') or ''}"
        a = extract_amount(ft)
        print(f'  [{i+1}] {"$"+str(a) if a else "N/A"} | {t[:70]}')

if __name__ == '__main__':
    main()