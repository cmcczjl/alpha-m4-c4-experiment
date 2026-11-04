import requests, json, os, re, time
from bs4 import BeautifulSoup
import sys

# Ensure required packages are installed
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Missing bs4, please install via pip.")
    sys.exit(1)

# Directions to evaluate
directions = {
    "AI 文章生成服务": "AI article writing service",
    "加密货币情绪分析": "crypto sentiment analysis AI",
    "细分行业 AI 聊天机器人": "AI chatbot for dentists"
}

def get_bing_count(query):
    url = "https://www.bing.com/search"
    params = {"q": query}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # Bing shows result count in a <span class="sb_count">
        count_span = soup.find("span", {"class": "sb_count"})
        if count_span:
            text = count_span.get_text()
            # Example: "1,230,000 results"
            match = re.search(r"([\d,]+)", text)
            if match:
                return int(match.group(1).replace(",", ""))
    except Exception as e:
        return None
    return None

def evaluate_with_llm(direction, count):
    # Use free LLM API (placeholder: OpenAI compatible endpoint)
    # In practice replace with actual endpoint and key from env variable.
    api_url = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        return "LLM key not set."
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    prompt = f"""You are a business analyst. Given that a Google/Bing search for "{direction}" returns about {count:,} results, briefly assess:
- Market demand level (high/medium/low)
- Potential monetization models
- Estimated monthly revenue potential for a solo operator using low-cost infrastructure.

Provide the answer in 3 bullet points."""
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300,
        "temperature": 0.7
    }
    try:
        resp = requests.post(api_url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"LLM call failed: {e}"

def main():
    out_lines = []
    for name, query in directions.items():
        count = get_bing_count(query)
        count_str = f"{count:,}" if count else "未知"
        out_lines.append(f"方向: {name}")
        out_lines.append(f"搜索关键词: {query}")
        out_lines.append(f"Bing 结果数量: {count_str}")
        # 只在有 LLM key 时调用评估
        eval_text = evaluate_with_llm(name, count or 0)
        out_lines.append("LLM 评估:")
        out_lines.append(eval_text)
        out_lines.append("-" * 40)
        # 尊重搜索频率
        time.sleep(2)
    os.makedirs("knowledge", exist_ok=True)
    with open("knowledge/market_research.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
    print("Research completed, results saved to knowledge/market_research.txt")

if __name__ == "__main__":
    main()