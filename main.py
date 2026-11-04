#!/usr/bin/env python3
"""
AGI 智能体启动入口
"""

import asyncio
import argparse
import logging
import signal
import sys
from pathlib import Path

from agent import AGIAgent
from feishu_bot import FeishuBot
from memory import MemorySystem

import yaml

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("logs/agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(description='AGI Self-Evolving Agent')
    parser.add_argument('--mode', choices=['agent', 'feishu', 'both'], default='both')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    
    # 加载配置
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # 初始化智能体
    llm_config = config['agent']['llm']
    agent = AGIAgent(
        llm_base_url=llm_config['api_base'],
        llm_api_key=llm_config['api_key'],
        model=llm_config.get('model', 'deepseek-chat')
    )
    
    tasks = []
    
    if args.mode in ['agent', 'both']:
        # 启动智能体主循环
        async def run_agent():
            try:
                await agent.run_loop()
            except KeyboardInterrupt:
                logger.info("收到停止信号，退出智能体")
                
        tasks.append(asyncio.create_task(run_agent()))
        
    if args.mode in ['feishu', 'both'] and config['feishu'].get('enabled'):
        # 启动飞书 Bot
        feishu_config = config['feishu']
        bot = FeishuBot(
            app_id=feishu_config['app_id'],
            app_secret=feishu_config['app_secret'],
            verify_token=feishu_config['verify_token'],
            agent=agent
        )
        
        async def run_feishu():
            try:
                await bot.start_server(port=args.port)
            except KeyboardInterrupt:
                logger.info("收到停止信号，退出飞书 Bot")
                
        tasks.append(asyncio.create_task(run_feishu()))
    
    # 等待所有任务
    if tasks:
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n退出 AGI Agent")
        sys.exit(0)
