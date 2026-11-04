#!/usr/bin/env python3
"""
Convert the trending GitHub repositories CSV (generated earlier) to JSON.
"""

import csv
import json
import sys
from pathlib import Path

def csv_to_json(csv_path: Path, json_path: Path):
    if not csv_path.is_file():
        print(f"CSV file not found: {csv_path}")
        sys.exit(1)

    with csv_path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = list(reader)

    # Convert numeric fields
    for item in data:
        if 'stargazers_count' in item:
            try:
                item['stargazers_count'] = int(item['stargazers_count'])
            except ValueError:
                pass

    with json_path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ JSON written to {json_path}")

if __name__ == "__main__":
    csv_file = Path(__file__).parent.parent / "trending_repos.csv"
    json_file = Path(__file__).parent.parent / "trending_repos.json"
    csv_to_json(csv_file, json_file)