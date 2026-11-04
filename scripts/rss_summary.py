#!/usr/bin/env python3
"""RSS 摘要工作流：抓取多个 RSS feed，生成带时间戳的摘要文件到 data/output/。"""
import os
import sys
import json
import hashlib
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_DIR = Path("data/output")
FEEDS = [
    {
        "name": "HackerNews-Frontpage",
        "url": "https://hnrss.org/frontpage",
    },
    {
        "name": "Python-Official",
        "url": "https://www.python.org/rss/feeds/",
    },
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
    },
]

MAX_ITEMS_PER_FEED = 5
TIMEOUT = 15


def fetch_feed(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (RSS-Summary/1.0)"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def parse_feed(raw: bytes, feed_name: str) -> list[dict]:
    """解析 RSS/Atom，返回前 N 条 item。"""
    items = []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        # 尝试去除 BOM / 非法字符
        cleaned = raw.decode("utf-8", errors="ignore").strip()
        try:
            root = ET.fromstring(cleaned)
        except ET.ParseError:
            return items

    # RSS 2.0: channel/item
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        desc = (item.findtext("description") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        link = (item.findtext("link") or "").strip()
        # 截断 description
        desc_short = desc[:200] + "..." if len(desc) > 200 else desc
        items.append({"title": title, "summary": desc_short, "date": pub, "link": link})
        if len(items) >= MAX_ITEMS_PER_FEED:
            break

    # Atom fallback
    if not items:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//atom:entry", ns):
            title = (entry.findtext("atom:title", namespaces=ns) or "").strip()
            summary_el = entry.find("atom:summary", ns)
            desc = (summary_el.text or "").strip() if summary_el is not None and summary_el.text else ""
            pub_el = entry.find("atom:published", ns) or entry.find("atom:updated", ns)
            pub = (pub_el.text or "").strip() if pub_el is not None and pub_el.text else ""
            link_el = entry.find("atom:link", ns)
            link = link_el.get("href", "") if link_el is not None else ""
            desc_short = desc[:200] + "..." if len(desc) > 200 else desc
            items.append({"title": title, "summary": desc_short, "date": pub, "link": link})
            if len(items) >= MAX_ITEMS_PER_FEED:
                break

    return items


def write_summary(feed_name: str, items: list[dict], source_url: str) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_name = feed_name.replace(" ", "_").replace("-", "_")
    fname = f"{safe_name}_{ts}.json"
    fpath = OUTPUT_DIR / fname

    payload = {
        "feed": feed_name,
        "source": source_url,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "item_count": len(items),
        "items": items,
    }
    fpath.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return fpath


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated = []
    errors = []

    for feed in FEEDS:
        name, url = feed["name"], feed["url"]
        try:
            raw = fetch_feed(url)
            items = parse_feed(raw, name)
            if not items:
                errors.append(f"{name}: 0 items parsed")
                continue
            fpath = write_summary(name, items, url)
            generated.append(str(fpath))
            print(f"[OK] {name} -> {fpath} ({len(items)} items)")
        except Exception as e:
            errors.append(f"{name}: {e}")
            print(f"[ERR] {name}: {e}", file=sys.stderr)

    # 汇总
    if generated:
        print(f"\n=== 共生成 {len(generated)} 个摘要文件 ===")
        for g in generated:
            print(f"  {g}")
    if errors:
        print(f"\n=== {len(errors)} 个 feed 出错 ===")
        for e in errors:
            print(f"  {e}", file=sys.stderr)

    # 退出码：至少 3 个成功才算通过
    sys.exit(0 if len(generated) >= 3 else 1)


if __name__ == "__main__":
    main()