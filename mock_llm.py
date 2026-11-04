"""
Mock LLM 适配器 - 用于测试框架
实际运行时替换为真实的 FREELLMAPI 调用
"""
import asyncio
import json
import random
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class ChatMessage:
    role: str
    content: str

@dataclass
class ChatCompletionResponse:
    choices: List[Dict]
    
    @property
    def message(self):
        return ChatMessage(**self.choices[0]['message'])

class MockLLM:
    """
    Mock LLM - 模拟 DeepSeek 响应
    用于测试智能体框架，不消耗 token
    """
    
    def __init__(self):
        self.call_count = 0
        self.model = "mock-deepseek"
        
    async def chat(self, messages: List[Dict], **kwargs) -> ChatCompletionResponse:
        """模拟聊天响应"""
        self.call_count += 1
        
        # 解析用户消息
        user_msg = ""
        for msg in messages:
            if msg.get('role') == 'user':
                user_msg = msg.get('content', '')
                break
                
        # 生成模拟回复
        reply = await self._generate_mock_reply(user_msg)
        
        return ChatCompletionResponse(choices=[{
            "message": {"role": "assistant", "content": reply}
        }])
        
    async def _generate_mock_reply(self, user_msg: str) -> str:
        """根据用户消息生成模拟回复"""
        
        # 命令处理
        if user_msg.strip() in ['/status', '/status']:
            return """📊 AGI 状态
━━━━━━━━━━━━━━━━
💰 当前资金: $1000.00
📈 今日决策: 0
🧪 待测假设: 2
✅ 已验证策略: 0
📚 失败教训: 0
⏱️ 运行时间: 0秒
━━━━━━━━━━━━━━━━
正在探索中..."""
            
        elif user_msg.strip() == '/help':
            return """🤖 AGI 智能体帮助

可用命令:
- /status - 查看运行状态
- /goals - 查看当前目标
- /learnings - 查看已积累教训
- /hypotheses - 查看假设列表
- /market - 查看市场数据

直接对话:
- 任何文字都会触发 AI 回复
- 可以询问市场分析
- 可以下达新目标
- 可以要求检查进度

记忆系统:
- 所有对话会记录到日记
- 失败教训会自动积累
- 成功模式会被放大"""
            
        elif '目标' in user_msg or 'goal' in user_msg.lower():
            return """🎯 当前目标分析

你的目标："在30天内赚到第一桶金100U"

评估：
- 时间窗口：30天 ✅ 可行
- 金额：100U ≈ $100 ✅ 合理
- 风险：需控制单次亏损 < 2%
- 策略：建议从低风险套利开始

下一步：
1. 观察市场机会（已完成）
2. 生成交易假设（进行中）
3. 小规模验证（待开始）
4. 扩大有效策略（长期）"""
            
        elif '交易' in user_msg or 'trade' in user_msg.lower():
            return """📈 交易分析

当前市场状态：
- BTC 4h趋势：下跌 -0.35%
- 恐惧贪婪指数：45（中性）
- 波动率：中等

我的发现：
1. 卖墙信号：LIT/USDT 出现大额卖单堆积
2. 资金费率：部分币种偏高，可能反向套利

假设已生成：
- hyp_1730000001: 卖墙反弹策略 (置信度 60%)
- hyp_1730000002: 资金费率套利 (置信度 50%)

需要我详细分析哪个假设？"""
            
        elif '教训' in user_msg or 'lesson' in user_msg.lower():
            return """📚 失败教训库

当前无教训记录。

这是正常的——我正在从零开始学习。

当遇到失败时，我会：
1. 分析失败原因
2. 记录触发条件
3. 避免重复犯错

预计 30-50 笔交易后会积累足够的教训。"""
            
        else:
            # 通用回复模板
            templates = [
                f"收到你的消息：「{user_msg[:50]}...」\n\n我正在分析这个问题。\n\n基于我的知识库和市场数据，有几个可能的方向：\n\n1. **市场观察**：当前 BTC 处于下跌趋势，但跌幅不大\n2. **机会识别**：可能存在的套利空间\n3. **风险可控**：单笔风险控制严格\n\n你想深入了解哪个方面？",
                
                f"好的，让我想想...\n\n作为经济学研究生，我看到：\n- 市场信息不对称带来机会\n- 但信息本身不会自动变现\n- 需要验证和执行\n\n当前有 {random.randint(1,3)} 个待测假设，要我详细说明吗？",
                
                f"你的问题触及了核心矛盾：\n\n知识 ≠ 盈利\n理解市场 ≠ 预测市场\n预测正确 ≠ 执行正确\n\n我正在通过以下方式缩小差距：\n- 小资金测试\n- 严格止损\n- 持续学习\n\n要看看当前进度吗？"
            ]
            
            return random.choice(templates)

# 兼容性包装
class MockAsyncOpenAI:
    """兼容 OpenAI SDK 接口的 Mock"""
    
    def __init__(self, base_url=None, api_key=None):
        self.chat = MockChat(self)
        
class MockChat:
    def __init__(self, client):
        self.completions = MockCompletions(client)
        
class MockCompletions:
    def __init__(self, client):
        self.client = client
        self.mock_llm = MockLLM()
        
    async def create(self, model, messages, temperature=0.7, max_tokens=2000, **kwargs):
        # 转换为标准格式
        result = await self.mock_llm.chat(messages, **kwargs)
        # 包装为 OpenAI 风格响应
        from openai.types.chat.chat_completion import ChatCompletion
        
        msg = {"role": "assistant", "content": result.message.content}
        choice = {"index": 0, "message": msg, "finish_reason": "stop"}
        
        # 创建响应对象
        completion = ChatCompletion(
            id="mock-id",
            object="chat.completion",
            created=int(time.time()),
            model=model,
            choices=[choice]
        )
        return completion
