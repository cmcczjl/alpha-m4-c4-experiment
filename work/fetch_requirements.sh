#!/usr/bin/env bash
set -euo pipefail

# Ensure output directory exists
mkdir -p data/market_research

# Fetch DuckDuckGo HTML results for Upwork workflow automation,
# filter lines containing "title" or "budget" (case‑insensitive),
# and keep only the first three matches.
curl -s -A "Mozilla/5.0" "https://html.duckduckgo.com/html/?q=upwork%20workflow%20automation%20site:upwork.com" \
    | grep -i -E "title|budget" -m 3 \
    > data/market_research/requirements.md