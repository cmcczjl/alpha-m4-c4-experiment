#!/usr/bin/env python3
import glob
import os

def verify_summaries():
    files = glob.glob('data/output/*.txt')
    print(f"Found {len(files)} files in data/output/")
    
    if not files:
        print("Error: No files found in data/output/")
        return False

    valid_count = 0
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                if content:
                    # Check if content contains a timestamp-like pattern (YYYY-MM-DD)
                    import re
                    if re.search(r'\d{4}-\d{2}-\d{2}', content):
                        print(f"[OK] {f}: Content length {len(content)}, Timestamp detected.")
                        valid_count += 1
                    else:
                        print(f"[WARN] {f}: Content found but no timestamp detected.")
                else:
                    print(f"[FAIL] {f}: File is empty.")
        except Exception as e:
            print(f"[ERROR] Reading {f}: {e}")

    print(f"\nSummary: {valid_count}/{len(files)} valid files.")
    return valid_count >= 3

if __name__ == "__main__":
    if verify_summaries():
        exit(0)
    else:
        exit(1)