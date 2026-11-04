#!/usr/bin/env python3
"""
GitHub Action helper: Fetch PR diff, send to OpenAI, post review comment.
"""

import os
import sys
import re
import json
import requests

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY")  # owner/repo
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if not all([GITHUB_TOKEN, REPO, OPENAI_KEY]):
    print("Required environment variables: GITHUB_TOKEN, GITHUB_REPOSITORY, OPENAI_API_KEY", file=sys.stderr)
    sys.exit(1)

OWNER, REPO_NAME = REPO.split("/")

def get_pr_number():
    """
    Extract PR number from GITHUB_REF like refs/pull/<number>/merge
    """
    ref = os.getenv("GITHUB_REF", "")
    m = re.search(r"refs/pull/(\d+)/", ref)
    if not m:
        # fallback: try GITHUB_EVENT_PATH
        event_path = os.getenv("GITHUB_EVENT_PATH")
        if event_path:
            with open(event_path) as f:
                data = json.load(f)
                return str(data.get("number"))
        print("Cannot determine PR number", file=sys.stderr)
        sys.exit(1)
    return m.group(1)

def fetch_diff(pr_number):
    url = f"https://api.github.com/repos/{OWNER}/{REPO_NAME}/pulls/{pr_number}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3.diff"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.text

def call_openai(diff_text):
    """
    Simple prompt: "Review the following PR diff and suggest comments:"
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful code review assistant."},
            {"role": "user", "content": f"Review the following PR diff and suggest concise comments:\n\n{diff_text[:2000]}"},
        ],
        "max_tokens": 500,
        "temperature": 0.2,
    }
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def post_comment(pr_number, body):
    url = f"https://api.github.com/repos/{OWNER}/{REPO_NAME}/pulls/{pr_number}/comments"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    payload = {"body": body, "commit_id": None, "path": None, "position": None}
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    print("Review comment posted.")
    return resp.json()

def main():
    pr_number = get_pr_number()
    print(f"Processing PR #{pr_number}")
    diff_text = fetch_diff(pr_number)
    print("Fetched diff, length:", len(diff_text))
    ai_comment = call_openai(diff_text)
    print("OpenAI response:", ai_comment[:200], "...")
    post_comment(pr_number, ai_comment)

if __name__ == "__main__":
    main()