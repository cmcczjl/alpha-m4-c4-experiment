```python
#!/usr/bin/env python3
"""
Simple Flask API that serves the trending GitHub repositories JSON.
"""

import json
from pathlib import Path

from flask import Flask, jsonify, abort

app = Flask(__name__)

# Load JSON once at startup
DATA_PATH = Path(__file__).parent.parent / "trending_repos.json"
if not DATA_PATH.is_file():
    raise FileNotFoundError(f"Data file not found: {DATA_PATH}")

with DATA_PATH.open("r", encoding="utf-8") as f:
    TRENDING_DATA = json.load(f)


@app.route("/trending", methods=["GET"])
def get_trending():
    """
    Return the list of trending repositories as JSON.
    """
    if not TRENDING_DATA:
        abort(404, description="No trending data available")
    return jsonify(TRENDING_DATA)


if __name__ == "__main__":
    # Run in debug mode for local testing
    app.run(host="0.0.0.0", port=5000, debug=True)
```
[FILE]
tools/test_api.py