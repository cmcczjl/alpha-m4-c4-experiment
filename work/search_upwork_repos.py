#!/usr/bin/env python3
"""搜索包含 Upwork FAQ 相关内容的 GitHub 仓库"""
import os
import json
import requests

def search_repos(query, limit=20):
    """使用 GitHub Search API 搜索仓库"""
    url = "https://api.github.com/search/repositories"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/5.37.36"
    }
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": limit
    }
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    data = response.json()
    items = data.get("items", [])
    
    results = []
    for item in items:
        results.append({
            "full_name": item["full_name"],
            "description": item.get("description", ""),
            "stars": item["stargazers_count"],
            "language": item.get("language", ""),
            "url": item["html_url"]
        })
    
    return results

if __name__ == "__main__":
    repos = search_repos("upwork faq", limit=15)
    
    # 保存结果到文件
    output_dir = "data/rag_corpus"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f"{output_dir}/upwork_repos.json", "w", encoding="utf-8") as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)
    
    print(f"找到 {len(repos)} 个仓库:")
    for repo in repos:
        print(f"  - {repo['full_name']} ({repo['stars']} stars)")
        if repo['description']:
            print(f"    {repo['description'][:100]}")
    
    print(f"\n结果已保存到: {output_dir}/upwork_repos.json")