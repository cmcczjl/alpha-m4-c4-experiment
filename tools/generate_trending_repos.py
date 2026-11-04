#!/usr/bin/env python3
"""
Generate a CSV file of the top GitHub repositories by stars.
"""

import csv
import json
import os
import sys
from datetime import datetime

import requests

def fetch_trending_repos(per_page=30, min_stars=10000):
    """
    Fetch trending repositories from GitHub API.

    Args:
        per_page (int): Number of repositories to fetch.
        min_stars (int): Minimum number of stars to filter.

    Returns:
        list[dict]: List of repository data dictionaries.
    """
    url = "https://api.github.com/search/repositories"
    params = {
        "q": f"stars:>={min_stars}",
        "sort": "stars",
        "order": "desc",
        "per_page": per_page,
        "page": 1,
    }
    headers = {
        "Accept": "application/vnd.github+json",
        # If you have a personal access token, you can add:
        # "Authorization": "token YOUR_TOKEN"
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        print(f"GitHub API returned status {response.status_code}")
        sys.exit(1)

    data = response.json()
    return data.get("items", [])


def write_csv(repos, filename="trending_repos.csv"):
    """
    Write repository data to a CSV file.

    Args:
        repos (list[dict]): Repository data.
        filename (str): Output CSV file path.
    """
    fieldnames = [
        "name",
        "full_name",
        "html_url",
        "stargazers_count",
        "language",
        "created_at",
        "updated_at",
        "description",
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for repo in repos:
            row = {
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "html_url": repo.get("html_url"),
                "stargazers_count": repo.get("stargazers_count"),
                "language": repo.get("language"),
                "created_at": repo.get("created_at"),
                "updated_at": repo.get("updated_at"),
                "description": repo.get("description") or "",
            }
            writer.writerow(row)
    print(f"CSV written to {filename}")


def main():
    print("Fetching trending repositories from GitHub...")
    repos = fetch_trending_repos()
    if not repos:
        print("No repositories fetched.")
        sys.exit(1)

    output_file = "trending_repos.csv"
    write_csv(repos, output_file)

    # Optionally, print the first few rows
    print("\nSample output:")
    with open(output_file, encoding="utf-8") as f:
        for i, line in enumerate(f):
            print(line.strip())
            if i >= 4:
                break


if __name__ == "__main__":
    main()