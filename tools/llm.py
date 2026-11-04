import os
import sys
import json

# 假设这里已经有了 API 配置，为了让脚本能跑通，我直接定义一个简单的 mock 函数
# 在实际环境中，它应该从环境变量或配置文件读取 API Key 并调用 LLM

def call_llm(prompt: str) -> str:
    """
    模拟调用 LLM 的函数。
    在实际生产中，这里会使用 requests 调用 OpenAI 或其他大模型 API。
    """
    # 为了保证 MVP 流程能跑通，我们直接返回一个预期的 JSON 格式字符串
    # 实际使用时，此处应替换为真正的 API 请求
    
    mock_response = {
        "review": [
            {
                "file": "app.py",
                "line": 5,
                "type": "bug",
                "message": "Potential bug: division by zero not handled.",
                "severity": "critical"
            },
            {
                "file": "app.py",
                "line": 10,
                "type": "style",
                "message": "Use type hints for better readability.",
                "severity": "minor"
            }
        ]
    }
    return json.dumps(mock_response)

# 检查是否有 __name__ 保护，确保作为模块导入时不会直接执行测试逻辑
if __name__ == "__main__":
    # 测试逻辑
    test_prompt = "Hello, test."
    print(f"Testing call_llm with prompt: {test_prompt}")
    result = call_llm(test_prompt)
    print(f"Result: {result}")