#!/usr/bin/env python3
import requests
import sys

def main():
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/Python_(programming_language)"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # 提取摘要作为有效文本片段
        text_content = data.get('extract', '')
        
        print("Markdown content saved:")
        print(f"Title: {data.get('title')}")
        print(f"Description: {data.get('description')}")
        print(f"Extract: {text_content}")
        
        # 验证有效文本
        if text_content and len(text_content) > 10:
            print("SUCCESS: Valid text fragment retrieved.")
        else:
            print("FAIL: Text fragment is empty or too short.")
            sys.exit(1)
            
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()