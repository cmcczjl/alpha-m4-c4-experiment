#!/usr/bin/env python3
import json
import os
import sys

FILE_PATH = "data/output/news_digest.json"

def main():
    if not os.path.isfile(FILE_PATH):
        print(f"ERROR: File not found: {FILE_PATH}")
        sys.exit(1)

    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR: Failed to parse JSON: {e}")
        sys.exit(1)

    if not isinstance(data, list):
        print("ERROR: JSON root is not a list")
        sys.exit(1)

    if len(data) < 3:
        print(f"ERROR: Expected at least 3 items, found {len(data)}")
        sys.exit(1)

    for i, item in enumerate(data, 1):
        if not isinstance(item, dict):
            print(f"ERROR: Item {i} is not an object")
            sys.exit(1)
        if "timestamp" not in item:
            print(f"ERROR: Item {i} missing 'timestamp'")
            sys.exit(1)
        if "summary" not in item:
            print(f"ERROR: Item {i} missing 'summary'")
            sys.exit(1)

    # If all checks pass, pretty‑print the JSON and signal success
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print("VALID")

if __name__ == "__main__":
    main()