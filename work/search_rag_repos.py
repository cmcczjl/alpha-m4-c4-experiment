import json
import urllib.request
import urllib.parse

def search_github_repos(query, limit=5):
    """
    使用 GitHub REST API 搜索仓库，作为 search_repos 工具的工程实现。
    """
    encoded_query = urllib.parse.quote(f"{query} stars:>100")
    url = f"https://api.github.com/search/repositories?q={encoded_query}&sort=stars&order=desc&per_page={limit}"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Mozilla/5.0"
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            items = data.get('items', [])
            return items
    except Exception as e:
        return [{"error": str(e)}]

def main():
    # 针对决策目标的关键词组合
    search_targets = [
        "RAG knowledge base",
        "private-gpt",
        "langchain-rag"
    ]
    
    all_results = {}
    print(f"{'Repository Name':<40} | {'Stars':<10} | {'Description'}")
    print("-" * 80)
    
    for target in search_targets:
        repos = search_github_repos(target, limit=3)
        for repo in repos:
            if "error" in repo:
                print(f"Error searching {target}: {repo['error']}")
                continue
            
            name = repo.get('full_name', 'N/A')
            stars = repo.get('stargazers_count', 0)
            desc = repo.get('description', '')[:50] + "..."
            print(f"{name:<40} | {stars:<10} | {desc}")
            
if __name__ == "__main__":
    main()