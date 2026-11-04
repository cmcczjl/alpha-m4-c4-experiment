#!/usr/bin/env python3
import subprocess, json, sys

query = "upwork faq site:github.com"
api_url = f"https://api.github.com/search/repositories?q={query}&per_page=5"
result = subprocess.run(['curl', '-s', api_url], capture_output=True, text=True)
if result.returncode != 0:
    print("Error fetching:", result.stderr, file=sys.stderr)
    sys.exit(1)

data = json.loads(result.stdout)
repo_urls = [item['html_url'] for item in data.get('items', [])]
for url in repo_urls:
    print(url)