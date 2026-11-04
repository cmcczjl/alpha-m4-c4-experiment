#!/usr/bin/env python3
"""Fetch top RSS items from 3 feeds and write to data/output/."""
import urllib.request
import xml.etree.ElementTree as ET
import os
import datetime
import ssl

def fetch_feed(url, max_items=2):
    """Fetch and parse an RSS/Atom feed, return list of (title, summary, link)."""
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = resp.read()
    except Exception as e:
        print(f"  [WARN] {url}: {e}")
        return []

    # Strip namespaces for simplicity
    data_clean = data.decode('utf-8', errors='ignore')
    items = []
    try:
        root = ET.fromstring(data_clean)
        # RSS 2.0
        for item in root.iter('item'):
            title = item.findtext('title') or ''
            desc = item.findtext('description') or ''
            link = item.findtext('link') or ''
            items.append((title.strip(), desc.strip()[:200], link.strip()))
            if len(items) >= max_items:
                break
        # Atom fallback
        if not items:
            ns = {'a': 'http://www.w3.org/2005/Atom'}
            for entry in root.findall('a:entry', ns):
                title = entry.findtext('a:title', default='', namespaces=ns)
                summary = entry.findtext('a:summary', default='', namespaces=ns)
                link_el = entry.find('a:link', ns)
                link = link_el.get('href', '') if link_el is not None else ''
                items.append((title.strip(), (summary or '')[:200], link.strip()))
                if len(items) >= max_items:
                    break
    except ET.ParseError as e:
        print(f"  [WARN] XML parse error for {url}: {e}")
    return items


def main():
    os.makedirs('data/output', exist_ok=True)
    urls = [
        'https://feeds.simplecast.com/5H0dKZ3L',
        'https://hnrss.org/frontpage',
        'https://www.techcrunch.com/feed/',
    ]

    all_items = []
    for url in urls:
        print(f"Fetching {url} ...")
        fetched = fetch_feed(url, max_items=2)
        print(f"  got {len(fetched)} items")
        all_items.extend(fetched)

    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    written = 0
    for i, (title, summary, link) in enumerate(all_items[:3]):
        safe_title = ''.join(c if c.isalnum() or c in '-_' else '_' for c in title[:40])
        fname = f"data/output/{ts}_{i}_{safe_title}.txt"
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(f"{title}\n{summary}\nsource:{link}\n")
        written += 1
        print(f"  wrote {fname}")

    print(f"Done. Wrote {written} items to data/output/")


if __name__ == '__main__':
    main()