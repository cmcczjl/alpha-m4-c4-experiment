```python
import os
import yaml
import requests
from flask import Flask, request, jsonify

# Load credentials once at startup
CRED_PATH = os.path.join(os.path.dirname(__file__), "data", "credentials.yaml")
with open(CRED_PATH) as f:
    cred = yaml.safe_load(f)

FREE_LLM_ENDPOINT = cred["free_llm"]["endpoint"]
FREE_LLM_API_KEY = cred["free_llm"]["api_key"]

app = Flask(__name__)

@app.route("/generate-title", methods=["POST"])
def generate_title():
    """
    Expects JSON: {"product_description": "..."}
    Returns JSON: {"title": "..."} or error info.
    """
    data = request.get_json()
    if not data or "product_description" not in data:
        return jsonify({"error": "Missing product_description"}), 400

    description = data["product_description"]
    prompt = (
        f"Generate a catchy, SEO‑friendly product title for the following description:\n"
        f"{description}\nTitle:"
    )

    # Call the free LLM API
    try:
        resp = requests.post(
            FREE_LLM_ENDPOINT,
            headers={
                "Authorization": f"Bearer {FREE_LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 20,
                "temperature": 0.7,
            },
            timeout=10,
        )
    except requests.RequestException as e:
        return jsonify({"error": "LLM request failed", "details": str(e)}), 502

    if resp.status_code != 200:
        return jsonify({"error": "LLM service error", "details": resp.text}), 502

    try:
        result = resp.json()
        title = result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return jsonify({"error": "Unexpected LLM response format", "details": str(e)}), 502

    return jsonify({"title": title})

if __name__ == "__main__":
    # For quick local testing
    app.run(host="0.0.0.0", port=5000)
```

[FILE]
test_app.py