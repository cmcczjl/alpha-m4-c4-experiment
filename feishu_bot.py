"""
飞书 Bot 适配器 - 使用 lark-oapi WebSocket 长连接模式
无需公网地址，直接在服务器上运行即可收发消息
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

import httpx
import yaml
from lark_oapi import EventDispatcherHandler
from lark_oapi.ws import Client as LarkWSClient
from lark_oapi.core.enum import LogLevel
from lark_oapi.api.im.v1.model.p2_im_message_receive_v1 import P2ImMessageReceiveV1
from lark_oapi.api.im.v1.model.event_message import EventMessage
from lark_oapi.api.im.v1.model.p2_im_chat_access_event_bot_p2p_chat_entered_v1 import (
    P2ImChatAccessEventBotP2pChatEnteredV1,
    P2ImChatAccessEventBotP2pChatEnteredV1Data,
)

logger = logging.getLogger(__name__)

# 加载配置
with open(Path(__file__).parent / "config.yaml", 'r', encoding='utf-8') as f:
    CONFIG = yaml.safe_load(f)

FEISHU_CFG = CONFIG['feishu']
APP_ID = FEISHU_CFG['app_id']
APP_SECRET = FEISHU_CFG['app_secret']
VERIFY_TOKEN = FEISHU_CFG.get('verify_token', '')
ENCRYPT_KEY = FEISHU_CFG.get('encryption_key', '')


class FeishuBot:
    """飞书 Bot - WebSocket 长连接模式"""
    
    def __init__(self, agent=None):
        self.agent = agent
        self.ws_client: Optional[LarkWSClient] = None
        self._access_token: Optional[str] = None
        self._token_expire: float = 0
    
    async def _get_access_token(self) -> Optional[str]:
        """获取 app_access_token"""
        if self._access_token and self._token_expire - 60 > asyncio.get_event_loop().time():
            return self._access_token
        
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                'https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal',
                json={'app_id': APP_ID, 'app_secret': APP_SECRET}
            )
            data = resp.json()
        
        if data.get('code') == 0:
            self._access_token = data['app_access_token']
            self._token_expire = asyncio.get_event_loop().time() + data.get('expire', 7200)
            return self._access_token
        return None
    
    async def send_message(self, receive_id: str, text: str, receive_id_type: str = "chat_id"):
        """发送消息"""
        token = await self._get_access_token()
        if not token:
            logger.error("无法获取 access token")
            return False
        
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                'https://open.feishu.cn/open-apis/im/v1/messages',
                headers={'Authorization': f'Bearer {token}'},
                params={'receive_id_type': receive_id_type},
                json={
                    'receive_id': receive_id,
                    'msg_type': 'text',
                    'content': json.dumps({'text': text})
                }
            )
            data = resp.json()
            if data.get('code') == 0:
                return True
            logger.error(f"发送消息失败: {data}")
            return False
    
    def _handle_event(self, data: P2ImMessageReceiveV1):
        """处理收到的消息事件（同步回调，内部转异步）"""
        try:
            logger.info(f"收到消息事件: message_id={getattr(data, 'message_id', 'unknown')}")
            # data 是 P2ImMessageReceiveV1，event 字段是 P2ImMessageReceiveV1Data
            event_data = getattr(data, 'event', None)
            if not event_data:
                logger.warning("收到空事件")
                return
            
            # event_data 是 P2ImMessageReceiveV1Data，真正的消息在 .message 字段
            msg = getattr(event_data, 'message', None)
            if not msg:
                logger.warning("event 中没有 message")
                return
            
            # msg 是 EventMessage
            chat_id = getattr(msg, 'chat_id', None)
            msg_type = getattr(msg, 'message_type', None)
            
            if not chat_id or msg_type != 'text':
                logger.info(f"非文本消息或无chat_id: chat_id={chat_id}, msg_type={msg_type}")
                return
            
            content = getattr(msg, 'content', '{}')
            if isinstance(content, str):
                content = json.loads(content)
            text = content.get('text', '')
            
            # 去掉 @mention
            text = text.strip()
            mentions = getattr(msg, 'mentions', None)
            if mentions:
                for mention in mentions:
                    name = getattr(mention, 'name', '')
                    if name:
                        text = text.replace(f"@{name}", "").strip()
            
            logger.info(f"收到消息: chat_id={chat_id}, text={text[:80]}")

            # ---- 指令: /approve <id> /reject <id>（人工介入审批）----
            import re as _re
            m = _re.match(r'^\s*/?(approve|reject)\s+(\S+)', text.strip())
            if m:
                action, int_id = m.group(1), m.group(2)
                try:
                    from memory_tiered import TieredMemory
                    mem = TieredMemory(Path(__file__).parent / "data")
                    mem.resolve_interrupt(int_id, action=action)
                    asyncio.create_task(self.send_message(chat_id,
                        f"✅ 已{'批准' if action == 'approve' else '拒绝'} {int_id}，α 将{'继续执行' if action == 'approve' else '取消并反思'}"))
                except Exception as e:
                    asyncio.create_task(self.send_message(chat_id, f"❌ 处理失败: {e}"))
                return

            # ---- 指令: /status ----
            if text.strip() in ("/status", "状态"):
                try:
                    from memory_tiered import TieredMemory
                    import json as _json
                    mem = TieredMemory(Path(__file__).parent / "data")
                    st = mem.stats()
                    state_file = Path(__file__).parent / "data" / "run_state.json"
                    rs = _json.loads(state_file.read_text()) if state_file.exists() else {}
                    last_trace_file = sorted((Path(__file__).parent / "data" / "cognitive_traces").glob("*.json"),
                                             key=lambda p: p.stat().st_mtime)
                    last = _json.loads(last_trace_file[-1].read_text()) if last_trace_file else {}
                    asyncio.create_task(self.send_message(chat_id,
                        f"📊 α 状态\n轮次: {rs.get('iterations', '?')} (焦点: {rs.get('roadmap_focus', '?')} × {rs.get('roadmap_focus_wheels', '?')}轮)\n"
                        f"记忆: {st}\n上轮: success={last.get('success')} | {(last.get('reflection') or '')[:100]}"))
                except Exception as e:
                    asyncio.create_task(self.send_message(chat_id, f"状态查询失败: {e}"))
                return

            # 记录最后的对话 chat_id（供自主循环发 [ASK] 用）
            try:
                (Path(__file__).parent / "data" / "last_chat_id.txt").write_text(chat_id, encoding='utf-8')
            except Exception:
                pass

            # 调用 agent
            if self.agent and hasattr(self.agent, 'chat'):
                asyncio.create_task(self._async_handle(chat_id, text))
            else:
                asyncio.create_task(self.send_message(chat_id, "探索者-α 还没准备好。"))

        except Exception as e:
            logger.error(f"处理消息失败: {e}", exc_info=True)
    
    def _handle_p2p_chat_entered(self, data: P2ImChatAccessEventBotP2pChatEnteredV1):
        """处理用户打开机器人私聊事件"""
        try:
            event = getattr(data, 'event', None)
            if event:
                chat_id = getattr(event, 'chat_id', None)
                user_id = getattr(getattr(event, 'operator', None), 'user_id', 'unknown')
                logger.info(f"用户打开私聊: chat_id={chat_id}, user_id={user_id}")
                if chat_id:
                    asyncio.create_task(self.send_message(chat_id, "你好！我是探索者-α，目标是赚钱，正在自主探索中。发送 /status 查看状态，或直接问我问题。"))
        except Exception as e:
            logger.error(f"处理私聊进入事件失败: {e}", exc_info=True)
    
    async def _async_handle(self, chat_id: str, text: str):
        """异步处理并回复"""
        try:
            reply = await self.agent.chat(text)
            await self.send_message(chat_id, reply)
        except Exception as e:
            logger.error(f"异步处理失败: {e}", exc_info=True)
            await self.send_message(chat_id, "抱歉，处理您的请求时出错。")
    
    def start(self):
        """启动 WebSocket 长连接（同步方法，内部会阻塞）"""
        logger.info(f"飞书 Bot 启动中... App ID: {APP_ID}")
        
        # 构建事件处理器
        builder = EventDispatcherHandler.builder(
            encrypt_key=ENCRYPT_KEY,
            verification_token=VERIFY_TOKEN,
        )
        
        builder.register_p2_im_message_receive_v1(self._handle_event)
        builder.register_p2_im_chat_access_event_bot_p2p_chat_entered_v1(self._handle_p2p_chat_entered)
        
        handler = builder.build()
        
        # 启动 WebSocket 客户端
        self.ws_client = LarkWSClient(
            app_id=APP_ID,
            app_secret=APP_SECRET,
            event_handler=handler,
            log_level=LogLevel.INFO,
            auto_reconnect=True,
        )
        
        logger.info("✅ 飞书 Bot WebSocket 已连接，等待消息...")
        self.ws_client.start()


def main():
    """测试入口"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    # 创建一个事件循环贯穿整个程序生命周期
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # 初始化 agent
    agent = None
    try:
        from agent import AGIAgent
        llm_cfg = CONFIG['agent']['llm']
        agent = AGIAgent(
            llm_base_url=llm_cfg['api_base'],
            llm_api_key=llm_cfg['api_key'],
            model=llm_cfg.get('model', 'auto')
        )
        loop.run_until_complete(agent.init_knowledge())
        logger.info("✅ AGI 智能体已连接")
    except Exception as e:
        logger.warning(f"AGI 智能体连接失败: {e}")
    
    bot = FeishuBot(agent=agent)
    bot.start()


if __name__ == '__main__':
    main()