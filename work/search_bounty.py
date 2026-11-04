#!/usr/bin/env python3
import os
import sys
import json
import requests

def main() -> None:
    # GitHub token for higher rate limits; optional
    token = os.getenv("GITHUB_TOKEN")
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"

    # Search query: bounty or help wanted labels, keywords n8n or automation
    query = 'label:"bounty" OR label:"help wanted" n8n OR automation'
    url = f"https://api.github.com/search/issues?q={query}&per_page=100"

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"GitHub API error: {resp.status_code}", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    items = data.get("items", [])[:3]  # take first 3 results

    leads = []
    for item in items:
        leads.append(
            {
                "url": item["html_url"],
                "title": item["title"],
                "description": item["body"][:200],  # truncate for brevity
            }
        )

    os.makedirs("data", exist_ok=True)
    with open("data/market_leads.json", "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2)

    print(f"Saved {len(leads)} leads to data/market_leads.json")

if __name__ == "__main__":
    main()