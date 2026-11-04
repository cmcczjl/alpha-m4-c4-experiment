#!/usr/bin/env python3
"""
AGI 智能体 - 本地测试脚本
使用 Mock LLM 模拟 AI 响应
"""

import asyncio
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from mock_llm import MockAsyncOpenAI
from agent import AGIAgent

async def test_agent():
    """测试智能体功能"""
    
    print("=" * 60)
    print("AGI 智能体 - 本地测试模式")
    print("使用 Mock LLM 模拟 DeepSeek 响应")
    print("=" * 60)
    
    # 初始化智能体（使用 Mock LLM）
    agent = AGIAgent(
        llm_base_url="http://mock.local/v1",
        llm_api_key="mock-key",
        model="mock-deepseek"
    )
    
    # 替换为 Mock LLM
    agent.client = MockAsyncOpenAI()
    
    print(f"\n✅ 智能体初始化完成")
    print(f"💰 初始资金: ${agent.capital:.2f}")
    print(f"🎯 目标: {agent.name}")
    
    # 初始化知识
    print("\n📚 初始化基础知识...")
    await agent.init_knowledge()
    print("✅ 知识库就绪")
    
    # 测试对话
    print("\n💬 对话测试...")
    test_messages = [
        "/status",
        "帮我分析一下今天的市场",
        "有什么交易机会？",
        "/help"
    ]
    
    for msg in test_messages:
        print(f"\n>>> {msg}")
        reply = await agent.chat(msg)
        print(f"<<< {reply[:100]}...")
    
    # 测试教训系统
    print("\n📚 教训系统测试...")
    lessons = agent.memory.load_lessons()
    print(f"  当前教训数: {len(lessons)}")
    
    # 添加一个教训
    agent.memory.save_lessons([
        {
            "hypothesis": "测试策略",
            "reason": "在震荡市中做空导致连续亏损",
            "keywords": ["震荡", "做空", "频繁"]
        }
    ])
    lessons = agent.memory.load_lessons()
    print(f"  ✅ 已添加新教训")
    print(f"  教训数: {len(lessons)}")
    
    print("\n" + "=" * 60)
    print("测试完成！框架运行正常。")
    print("=" * 60)
    
    print("\n下一步：")
    print("1. 配置你的 FREELLMAPI 地址")
    print("2. 更新 config.yaml 中的 api_base 和 api_key")
    print("3. 重启智能体以启用真实 AI")

if __name__ == "__main__":
    asyncio.run(test_agent())
