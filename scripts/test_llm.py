import os, json, pathlib, sys
import requests
import yaml

def load_credentials():
    cred_path = pathlib.Path('data/credentials.yaml')
    if not cred_path.exists():
        print("Credentials file missing", file=sys.stderr)
        sys.exit(1)
    with cred_path.open('r') as f:
        return yaml.safe_load(f)

def call_llm(prompt: str) -> str:
    creds = load_credentials()
    api_key = creds['free_llm']['api_key']
    endpoint = creds['free_llm']['endpoint']
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-3.5-turbo",   # 假设模型名，实际可根据 API 文档调整
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200
    }
    resp = requests.post(endpoint, headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    # 假设返回结构为 {"choices": [{"message": {"content": "..."} }]}
    try:
        content = data["choices"][0]["message"]["content"]
    except Exception:
        content = json.dumps(data, ensure_ascii=False, indent=2)
    return content

def main():
    prompt = "请用中文简短介绍一下什么是生成式人工智能以及它的主要应用场景。"
    try:
        response = call_llm(prompt)
    except Exception as e:
        response = f"调用大模型失败: {e}"
    out_path = pathlib.Path('knowledge/llm_response.md')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(response, encoding='utf-8')
    print(f"LLM response 已写入 {out_path}")

if __name__ == "__main__":
    main()