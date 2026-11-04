#!/usr/bin/env python3
"""
探索者-α 启动器 - 自主进化模式
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import yaml
from agent import AGIAgent
from autonomous import AutonomousLoop

def setup_logging():
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    # 清空已有 handler（防止重复）
    for h in logging.root.handlers[:]:
        logging.root.removeHandler(h)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "autonomous.log", encoding='utf-8'),
            # 注意：不加大 stdout 的 StreamHandler —— 启动器已把 stdout 重定向到同一日志文件，
            # 再加 StreamHandler 会导致每行写两次（FileHandler + stdout→文件）。
        ]
    )

async def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    with open(Path(__file__).parent / "config.yaml") as f:
        config = yaml.safe_load(f)
    
    llm_cfg = config['agent']['llm']
    
    agent = AGIAgent(
        llm_base_url=llm_cfg['api_base'],
        llm_api_key=llm_cfg['api_key'],
        model=llm_cfg.get('model', 'auto')
    )
    
    await agent.init_knowledge()
    
    loop = AutonomousLoop(agent)
    
    interval = 30  # 分钟
    
    stop_event = asyncio.Event()
    
    def handle_stop(signum, frame):
        logger.info("收到停止信号")
        loop.stop()
        stop_event.set()
    
    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)
    
    logger.info("=" * 50)
    logger.info(f"探索者-α 启动，进入自主进化模式")
    logger.info(f"目标: {config['agent']['initial_goal']}")
    logger.info(f"每 {interval} 分钟自主行动一次")
    logger.info("=" * 50)
    
    tasks = [asyncio.create_task(loop.run(interval))]
    tasks.append(asyncio.create_task(stop_event.wait()))
    await asyncio.gather(*tasks)
    logger.info("探索者-α 已停止")

if __name__ == "__main__":
    asyncio.run(main())
