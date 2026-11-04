```python
import json
from app import app

def test_generate_title():
    client = app.test_client()
    payload = {
        "product_description": "A lightweight waterproof hiking backpack with 30L capacity and ergonomic straps."
    }
    response = client.post(
        "/generate-title",
        data=json.dumps(payload),
        content_type="application/json"
    )
    print("Status code:", response.status_code)
    print("Response JSON:", response.get_json())

if __name__ == "__main__":
    test_generate_title()
```

knowledge/ideas.md