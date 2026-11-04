#!/usr/bin/env python3
"""
AGI 智能体 - 真实 API 测试
使用宿主机上的 FREELLMAPI
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent import AGIAgent

async def test_agent():
    print("=" * 60)
    print("AGI 智能体 - 真实 API 测试")
    print("使用宿主机 FREELLMAPI (172.17.0.1:3001)")
    print("=" * 60)
    
    # 初始化智能体（使用真实 API）
    agent = AGIAgent(
        llm_base_url="http://172.17.0.1:3001",
        llm_api_key="freellmapi-94c04f08fa660f14e4a4c3723ca76b2d9dbe83593caa4c15",
        model="auto"
    )
    
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
        "用一句话说明什么是市场微观结构",
        "有什么交易机会？",
    ]
    
    for msg in test_messages:
        print(f"\n>>> {msg}")
        reply = await agent.chat(msg)
        print(f"<<< {reply[:150]}...")
    
    # 测试教训系统
    print("\n📚 教训系统测试...")
    lessons = agent.memory.load_lessons()
    print(f"  当前教训数: {len(lessons)}")
    
    print("\n" + "=" * 60)
    print("测试完成！真实 AI 已对接。")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_agent())
