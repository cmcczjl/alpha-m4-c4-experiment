"""
LangGraph Checkpointer 集成 - 替换原有 TieredMemory
参考 LangGraph v0.2+: SqliteSaver 做 checkpoint 持久化
能力：
  - 每轮自动存 checkpoint（含完整 state）
  - 时间旅行：回滚到任意历史轮次
  - 人工介入：interrupt() 暂停等用户确认
  - 跨线程长期记忆：通过 base_store 跨 session 共享
"""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata

logger = logging.getLogger(__name__)

DB_PATH = "data/checkpoints.sqlite"


class LangGraphMemory:
    """
    把原有 TieredMemory 的接口迁移到 LangGraph Checkpointer。
    用 thread_id=agent_main 区分主循环，未来可开子线程。
    """
    def __init__(self, base_path: Path):
        self.db_path = base_path / DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # SqliteSaver(conn) 直接持连接（from_conn_string 是 context manager，需 with）
        self._ctx = SqliteSaver.from_conn_string(str(self.db_path))
        self.saver = self._ctx.__enter__()
        self.thread_id = "agent_main"
        self.current_state: Dict = {}

    # ---- 兼容旧接口 ----
    def retrieve(self, tier: str = None, tags: List[str] = None, limit: int = 10) -> List:
        """
        从 checkpoint history 里取最近 N 条。
        为兼容旧代码，返回 MockEntry 对象（.content = state）。
        """
        class MockEntry:
            def __init__(self, content):
                self.content = content
        history = []
        for checkpoint, meta, _ in self.saver.list({"configurable": {"thread_id": self.thread_id}}, limit=limit):
            state = checkpoint.get("channel_values", {})
            history.append(MockEntry(state))
        return history

    def store(self, tier: str, content: Dict, tags: List[str] = None, importance: float = 1.0) -> str:
        """存一条工作记忆 → 写入 checkpoint"""
        self.current_state.update(content)
        self._save_checkpoint(self.current_state)
        return f"stored_{tier}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def stats(self) -> Dict:
        """返回 checkpoint 数量"""
        cnt = 0
        for _ in self.saver.list({"configurable": {"thread_id": self.thread_id}}, limit=9999):
            cnt += 1
        return {"checkpoints": cnt}

    def get_procedural_skills(self) -> List:
        """从 state 里取 skills 字段"""
        return self.current_state.get("skills", [])

    def consolidate_working_to_episodic(self, episode_id: str, data: Dict):
        """工作记忆 → 情景：直接存 checkpoint"""
        self.current_state.setdefault("episodes", []).append({episode_id: data})
        self._save_checkpoint(self.current_state)

    # ---- LangGraph 专有 ----
    def _save_checkpoint(self, state: Dict):
        """保存当前 state 为 checkpoint"""
        config = {"configurable": {"thread_id": self.thread_id}}
        checkpoint: Checkpoint = {
            "v": 1,
            "ts": datetime.now().isoformat(),
            "id": f"chk_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "channel_values": state,
        }
        meta: CheckpointMetadata = {"source": "autonomous_loop", "step": len(list(self.saver.list(config, limit=9999)))}
        self.saver.put(config, checkpoint, meta, {})
        logger.debug(f"checkpoint saved: {checkpoint['id']}")

    def get_latest_state(self) -> Dict:
        """取最新 checkpoint 的 state"""
        config = {"configurable": {"thread_id": self.thread_id}}
        latest = self.saver.get(config)
        if latest:
            return latest.get("channel_values", {})
        return {}

    def rollback_to(self, checkpoint_id: str) -> bool:
        """时间旅行：回滚到指定 checkpoint（需要应用层重新加载 state）"""
        config = {"configurable": {"thread_id": self.thread_id}}
        chk = self.saver.get_tuple(config, checkpoint_id)
        if chk:
            self.current_state = chk.checkpoint.get("channel_values", {})
            logger.info(f"rollback to {checkpoint_id}")
            return True
        return False

    def interrupt(self, reason: str) -> str:
        """
        人工介入：写入 interrupt 标记，应用层需检测并暂停。
        返回 interrupt_id，供外部确认。
        """
        int_id = f"int_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.current_state["_interrupt"] = {"id": int_id, "reason": reason, "at": datetime.now().isoformat()}
        self._save_checkpoint(self.current_state)
        logger.warning(f"INTERRUPT: {reason} ({int_id})")
        return int_id

    def resume_after_interrupt(self, int_id: str, user_input: Dict):
        """用户确认后清除 interrupt 标记，写入用户反馈"""
        if "_interrupt" in self.current_state and self.current_state["_interrupt"]["id"] == int_id:
            del self.current_state["_interrupt"]
            self.current_state.setdefault("user_feedbacks", []).append(user_input)
            self._save_checkpoint(self.current_state)
            logger.info(f"resumed after {int_id}")
            return True
        return False

    def close(self):
        self.saver.conn.close()


def create_memory(base_path: Path) -> LangGraphMemory:
    """工厂函数，返回实例（目前最小化：维持原有字典行为）"""
    return LangGraphMemory(base_path)
