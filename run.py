#!/usr/bin/env python3
"""
AGI 智能体 - 生产启动脚本
配置 FREELLMAPI 后直接运行
"""

import asyncio
import sys
from pathlib import Path
import yaml
import logging
import signal

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from agent import AGIAgent
from freellm_llm import FreellmLLM
from feishu_bot import FeishuBot

# 配置日志
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
    # 加载配置
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    agent_config = config['agent']
    llm_config = agent_config['llm']
    feishu_config = config['feishu']
    
    # 初始化智能体
    agent = AGIAgent(
        llm_base_url=llm_config['api_base'],
        llm_api_key=llm_config['api_key'],
        model=llm_config.get('model', 'deepseek-chat')
    )
    
    # 替换为真实 LLM
    agent.llm = FreellmLLM(
        api_base=llm_config['api_base'],
        api_key=llm_config['api_key'],
        model=llm_config.get('model', 'deepseek-chat')
    )
    
    logger.info("=" * 60)
    logger.info("AGI 智能体启动")
    logger.info(f"目标: {agent_config['initial_goal']}")
    logger.info(f"初始资金: ${agent.capital:.2f}")
    logger.info(f"LLM: {llm_config['api_base']}")
    logger.info("=" * 60)
    
    # 初始化知识
    await agent.init_knowledge()
    
    tasks = []
    
    # 启动智能体主循环
    async def run_agent():
        try:
            await agent.run_loop()
        except KeyboardInterrupt:
            logger.info("收到停止信号，退出智能体")
    
    tasks.append(asyncio.create_task(run_agent()))
    
    # 启动飞书 Bot
    if feishu_config.get('enabled'):
        bot = FeishuBot(
            app_id=feishu_config['app_id'],
            app_secret=feishu_config['app_secret'],
            verify_token=feishu_config['verify_token'],
            agent=agent
        )
        
        async def run_feishu():
            try:
                port = feishu_config.get('port', 8000)
                await bot.start_server(port=port)
            except KeyboardInterrupt:
                logger.info("收到停止信号，退出飞书 Bot")
        
        tasks.append(asyncio.create_task(run_feishu()))
        logger.info(f"飞书 Bot 运行中: http://0.0.0.0:{port}/feishu/webhook")
    
    # 等待所有任务
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n退出 AGI Agent")
        sys.exit(0)
