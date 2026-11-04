#!/usr/bin/env python3
"""
GitHub 工具 - 探索者-α 操作 GitHub
功能：搜索 issues、搜索仓库、获取 bounty
通过 credential_proxy 调用，不直接读取凭证文件
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from tool_registry import tool
from tools.credential_proxy import _creds, _check_host

import httpx


def _github_headers() -> dict:
    """从凭证代理获取 GitHub 认证头"""
    c = _creds().get("github", {})
    token = c.get("token")
    if not token:
        raise RuntimeError("github token 未配置")
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}


def _github_get(url: str, params: dict = None) -> dict:
    """统一 GET 请求，自动注入 token 并校验域名"""
    if not _check_host(url):
        return {"error": "域名不在白名单"}
    try:
        r = httpx.get(url, params=params, headers=_github_headers(), timeout=15)
        if r.status_code >= 400:
            return {"error": f"API 错误 {r.status_code}: {r.text[:200]}"}
        return r.json()
    except Exception as e:
        return {"error": str(e)}


@tool(description="搜索有 bounty/need-help 标签的 GitHub issues，适合拿赏金。",
      category="github",
      when_not_to_use="搜索普通 issues、搜索仓库、查看用户信息",
      disambiguation="专门搜索 bounty/悬赏任务；普通 issue 搜索用 search_issues，仓库搜索用 search_repos")
def search_bounties(query: str, limit: int = 10):
    """搜索有 bounty/需要帮助的 issues"""
    url = "https://api.github.com/search/issues"
    params = {
        "q": f"{query} is:issue is:open label:\"help wanted\"",
        "sort": "created",
        "order": "desc",
        "per_page": limit,
    }
    data = _github_get(url, params)
    if "error" in data:
        return data
    items = data.get("items", [])
    results = []
    for item in items:
        results.append({
            "repo": f"{item['repository_url'].split('/')[-2]}/{item['repository_url'].split('/')[-1]}",
            "number": item["number"],
            "title": item["title"],
            "url": item["html_url"],
            "labels": [l["name"] for l in item.get("labels", [])],
            "author": item["user"]["login"],
            "created": item["created_at"][:10],
        })
    return {"count": len(results), "issues": results}


@tool(description="搜索 GitHub 仓库（按星数/关键词），适合找目标项目。",
      category="github",
      when_not_to_use="搜索 issues、搜索代码、查看用户信息",
      disambiguation="搜索仓库元数据；搜索 issues 用 search_issues，搜索 bounty 用 search_bounties")
def search_repos(query: str, limit: int = 10):
    url = "https://api.github.com/search/repositories"
    params = {"q": query, "sort": "stars", "order": "desc", "per_page": limit}
    data = _github_get(url, params)
    if "error" in data:
        return data
    items = data.get("items", [])
    return [{"full_name": i["full_name"], "stars": i["stargazers_count"],
             "url": i["html_url"], "desc": i.get("description", "")[:100]} for i in items]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"usage": "search-bounty <query> | search-repo <query>"}))
    elif sys.argv[1] == "search-bounty":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "help wanted"
        print(json.dumps(search_bounties(query), ensure_ascii=False, indent=2))
    elif sys.argv[1] == "search-repo":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "python"
        print(json.dumps(search_repos(query), ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"error": "未知命令"}))
