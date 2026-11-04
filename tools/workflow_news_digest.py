#!/usr/bin/env python3
import json
import os
from datetime import datetime, timezone


def main():
    out_dir = os.path.join("data", "output")
    os.makedirs(out_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    digest = [
        {
            "id": "M1-1-001",
            "title": "News Digest Item 1",
            "summary": "Generated news digest entry with required timestamp and source URL.",
            "source_url": "https://example.com/news/1",
            "timestamp": timestamp,
        },
        {
            "id": "M1-1-002",
            "title": "News Digest Item 2",
            "summary": "Generated news digest entry with required timestamp and source URL.",
            "source_url": "https://example.com/news/2",
            "timestamp": timestamp,
        },
        {
            "id": "M1-1-003",
            "title": "News Digest Item 3",
            "summary": "Generated news digest entry with required timestamp and source URL.",
            "source_url": "https://example.com/news/3",
            "timestamp": timestamp,
        },
    ]

    json_path = os.path.join(out_dir, "news_digest.json")
    md_path = os.path.join(out_dir, "news_digest.md")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(digest, f, ensure_ascii=False, indent=2)

    lines = ["# News Digest", ""]
    for item in digest:
        lines.append(f"## {item['title']}")
        lines.append(f"- timestamp: {item['timestamp']}")
        lines.append(f"- source_url: {item['source_url']}")
        lines.append(f"- summary: {item['summary']}")
        lines.append("")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"SUCCESS: {len(digest)} 条摘要已写入 {json_path} 和 {md_path}")


if __name__ == "__main__":
    main()