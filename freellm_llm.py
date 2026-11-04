"""
真实 LLM 适配器 - 对接 FREELLMAPI
"""
import os
import httpx
import json
from typing import List, Dict, Any

class FreellmLLM:
    """FREELLMAPI 适配器"""
    
    def __init__(self, api_base: str, api_key: str, model: str = "auto"):
        self.api_base = api_base.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.client = httpx.AsyncClient(base_url=api_base, timeout=120)
        
    async def chat(self, messages, **kwargs):
        """调用 FREELLMAPI"""
        
        # 构建请求
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get('temperature', 0.7),
            "max_tokens": kwargs.get('max_tokens', 2000)
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # 直接调用 API
            resp = await self.client.post(
                f"{self.api_base}/v1/chat/completions",
                json=payload,
                headers=headers
            )
            resp.raise_for_status()
            
            # 解析响应
            import json
            data = resp.json()
            
            # 兼容不同格式
            if isinstance(data, dict):
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            else:
                content = str(data)
            
            return {"role": "assistant", "content": content}
            
        except Exception as e:
            print(f"FREELLMAPI 错误: {e}")
            return {"role": "assistant", "content": f"[系统错误] {str(e)}"}
            
    async def close(self):
        await self.client.aclose()
