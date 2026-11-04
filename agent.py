"""
AGI 智能体核心 - 探索者-α
LLM 客户端封装 + 飞书对话接口
记忆/认知/进化由 autonomous.py 的子系统负责
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

import httpx
import yaml
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config.yaml"
DATA_DIR = Path(__file__).parent / "data"


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

CONFIG = load_config()


class AGIAgent:
    """AGI 智能体核心 - LLM 客户端封装"""

    def __init__(self, llm_base_url: str, llm_api_key: str, model: str = "auto"):
        self.llm_base_url = llm_base_url
        self.llm_api_key = llm_api_key
        self.model = model
        self.name = CONFIG['agent'].get('name', '探索者-α')

        # 初始化 OpenAI 客户端（使用正确的 base URL）
        self.client = AsyncOpenAI(
            base_url=f"{llm_base_url}/v1",
            api_key=llm_api_key
        )

    async def init_knowledge(self):
        """初始化知识库（占位，由认知循环负责）"""
        pass

    async def close(self):
        """关闭资源"""
        try:
            await self.client.close()
        except Exception:
            pass

    async def chat(self, message: str) -> str:
        """处理用户消息（飞书对话用）"""
        from memory_tiered import create_memory
        memory = create_memory(DATA_DIR)

        # 检索相关记忆
        relevant = memory.retrieve(tier="episodic", limit=5)
        relevant_text = "\n".join(
            f"- {json.dumps(r.content, ensure_ascii=False)[:200]}" for r in relevant
        ) or "暂无相关记忆"

        # 语义陷阱（对话时也提醒）
        traps = memory.retrieve(tier="semantic", tags=["trap"], limit=5)
        trap_text = "\n".join(
            f"- 陷阱: {t.content.get('pattern', '')[:60]}" for t in traps
        ) or "（无）"

        # 构建系统提示
        system_prompt = f"""你是 {self.name}。

{CONFIG['agent'].get('persona', '').strip()}

【财产安全与法律风险红线】
任何涉及真实资金流动、合同、实名、KYC、私钥的操作，必须提醒主人确认后才能做。
不保存不明来源的凭证，不点击不明链接。

**目标**: {CONFIG['agent']['initial_goal']}

**近期记忆：**
{relevant_text}

**已知陷阱：**
{trap_text}

请基于以上信息回答用户的问题。保持简洁、专业、实事求是。"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            if hasattr(response, 'choices') and response.choices:
                reply = response.choices[0].message.content
            elif isinstance(response, dict) and 'choices' in response:
                reply = response['choices'][0]['message']['content']
            else:
                reply = str(response)

            return reply

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return f"[系统错误] 无法处理请求: {str(e)}"