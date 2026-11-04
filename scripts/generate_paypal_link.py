import pathlib, json, sys, base64, time
import requests
import yaml

CRED_PATH = pathlib.Path('data/credentials.yaml')
OUT_PATH = pathlib.Path('knowledge/paypal_order.md')
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

def load_credentials():
    if not CRED_PATH.exists():
        print("Credentials file missing", file=sys.stderr)
        sys.exit(1)
    with CRED_PATH.open('r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_paypal_access_token(creds):
    """使用 client_id/secret 换取 OAuth2 访问令牌"""
    client_id = creds['paypal']['client_id']
    secret = creds['paypal']['secret']
    sandbox = creds['paypal'].get('sandbox', True)

    token_url = ("https://api-m.sandbox.paypal.com/v1/oauth2/token"
                 if sandbox else "https://api-m.paypal.com/v1/oauth2/token")
    auth = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    resp = requests.post(token_url, headers=headers, data=data, timeout=15)
    resp.raise_for_status()
    return resp.json()["access_token"]

def create_order(access_token, creds, amount="5.00", currency="USD", description="LLM‑as‑a‑Service"):
    sandbox = creds['paypal'].get('sandbox', True)
    order_url = ("https://api-m.sandbox.paypal.com/v2/checkout/orders"
                 if sandbox else "https://api-m.paypal.com/v2/checkout/orders")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {
                "currency_code": currency,
                "value": amount
            },
            "description": description
        }],
        "application_context": {
            "brand_name": "LLM‑Service",
            "landing_page": "BILLING",
            "user_action": "PAY_NOW",
            "return_url": "https://example.com/paypal/success",
            "cancel_url": "https://example.com/paypal/cancel"
        }
    }
    resp = requests.post(order_url, headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    order = resp.json()
    # 从返回中提取批准链接
    approve_link = None
    for link in order.get("links", []):
        if link.get("rel") == "approve":
            approve_link = link.get("href")
            break
    if not approve_link:
        raise RuntimeError("未找到批准链接")
    return approve_link, order["id"]

def main():
    creds = load_credentials()
    try:
        token = get_paypal_access_token(creds)
        link, order_id = create_order(token, creds)
        OUT_PATH.write_text(f"PayPal Order ID: {order_id}\\nApprove Link: {link}\\n", encoding='utf-8')
        print(f"PayPal 付款链接已写入 {OUT_PATH}")
    except Exception as e:
        OUT_PATH.write_text(f"生成付款链接失败: {e}\\n", encoding='utf-8')
        print(f"错误: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()