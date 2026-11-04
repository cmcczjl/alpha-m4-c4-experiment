"""
三层记忆系统 - 参考 SecondBrain / AgentOS / OpenHands
- Working Memory: 线程级检查点，短期上下文
- Episodic Memory: 按天/会话的情景记忆，含反思
- Semantic Memory: 结构化知识图谱、策略库、技能模式
- Procedural Memory: 可执行技能、工具模式、解题套路
"""
import json
import sqlite3
import threading
from pathlib import Path
from datetime import datetime, date
from typing import Any, Optional, List, Dict
from dataclasses import dataclass, asdict, field
import hashlib

@dataclass
class MemoryEntry:
    id: str
    tier: str  # working, episodic, semantic, procedural
    content: Dict[str, Any]
    tags: List[str] = field(default_factory=list)
    importance: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    accessed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0

class TieredMemory:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.db_path = base_path / "memory.db"
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    tier TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT,
                    importance REAL DEFAULT 1.0,
                    created_at TEXT NOT NULL,
                    accessed_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tier ON memories(tier)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tags ON memories(tags)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance DESC)")
    
    def _gen_id(self, tier: str, content: Dict) -> str:
        import uuid
        h = hashlib.md5(f"{tier}{json.dumps(content, sort_keys=True)}".encode()).hexdigest()[:8]
        return f"{tier}_{h}_{uuid.uuid4().hex[:4]}"
    
    def store(self, tier: str, content: Dict, tags: List[str] = None, importance: float = 1.0) -> str:
        """存储记忆，返回ID"""
        mid = self._gen_id(tier, content)
        entry = MemoryEntry(
            id=mid, tier=tier, content=content,
            tags=tags or [], importance=importance
        )
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO memories 
                    (id, tier, content, tags, importance, created_at, accessed_at, access_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (mid, tier, json.dumps(content), json.dumps(tags or []), importance,
                      entry.created_at, entry.accessed_at, 0))
        return mid
    
    def retrieve(self, tier: str = None, tags: List[str] = None, 
                 min_importance: float = 0, limit: int = 50) -> List[MemoryEntry]:
        """检索记忆"""
        query = "SELECT * FROM memories WHERE importance >= ?"
        params = [min_importance]
        if tier:
            query += " AND tier = ?"
            params.append(tier)
        if tags:
            for tag in tags:
                query += " AND tags LIKE ?"
                params.append(f"%{tag}%")
        query += " ORDER BY importance DESC, accessed_at DESC LIMIT ?"
        params.append(limit)
        
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(query, params).fetchall()
        
        results = []
        for row in rows:
            entry = MemoryEntry(
                id=row['id'], tier=row['tier'],
                content=json.loads(row['content']),
                tags=json.loads(row['tags']),
                importance=row['importance'],
                created_at=row['created_at'],
                accessed_at=row['accessed_at'],
                access_count=row['access_count']
            )
            # 更新访问统计
            self._touch(entry.id)
            results.append(entry)
        return results
    
    def _touch(self, mid: str):
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE memories SET accessed_at = ?, access_count = access_count + 1
                    WHERE id = ?
                """, (datetime.now().isoformat(), mid))
    
    def consolidate_working_to_episodic(self, thread_id: str, summary: Dict):
        """工作记忆 → 情景记忆（每日/每会话调用）"""
        # 从 working 检索该线程的所有记忆
        working = self.retrieve(tier="working", tags=[thread_id], limit=200)
        if not working:
            return
        
        # 生成情景记忆条目
        episodic_content = {
            "thread_id": thread_id,
            "summary": summary,
            "events": [w.content for w in working],
            "lessons": [w.content for w in working if "lesson" in (w.tags or [])],
            "decisions": [w.content for w in working if "decision" in (w.tags or [])],
            "duration_hours": len(working) * 0.5  # 估算
        }
        today = date.today().isoformat()
        self.store("episodic", episodic_content, 
                   tags=[today, thread_id], importance=2.0)
        
        # 标记 working 为已归档（不删除，保留近期上下文）
        # 实际可定期清理旧 working
    
    def extract_semantic_patterns(self, min_occurrences: int = 3) -> List[Dict]:
        """从情景记忆提取语义模式（技能/策略/规律）"""
        episodic = self.retrieve(tier="episodic", limit=500)
        if len(episodic) < min_occurrences:
            return []
        
        # 简单模式提取：高频标签组合、成功/失败模式
        patterns = {}
        for e in episodic:
            for tag in e.tags:
                patterns[tag] = patterns.get(tag, 0) + 1
        
        # 存储为语义记忆
        semantic_entries = []
        for tag, count in patterns.items():
            if count >= min_occurrences:
                content = {"pattern": tag, "frequency": count, "source": "episodic_extraction"}
                mid = self.store("semantic", content, tags=["pattern", tag], importance=count/10)
                semantic_entries.append({"id": mid, "pattern": tag, "freq": count})
        return semantic_entries
    
    def get_procedural_skills(self, category: str = None) -> List[Dict]:
        """获取程序性记忆（可执行技能）"""
        return self.retrieve(tier="procedural", tags=[category] if category else None, limit=100)
    
    def save_skill(self, name: str, code: str, description: str, 
                   category: str, params_schema: Dict = None) -> str:
        """保存可执行技能到程序性记忆"""
        content = {
            "name": name,
            "code": code,
            "description": description,
            "category": category,
            "params_schema": params_schema or {},
            "version": 1,
            "success_count": 0,
            "failure_count": 0
        }
        return self.store("procedural", content, tags=["skill", category], importance=5.0)
    
    def update_skill_stats(self, skill_id: str, success: bool):
        """更新技能成功/失败统计"""
        entries = self.retrieve(tier="procedural", limit=1)
        # 实际实现需查询后更新，简化版
        pass
    
    def stats(self) -> Dict:
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT tier, COUNT(*) as count FROM memories GROUP BY tier")
                return {row[0]: row[1] for row in cursor.fetchall()}

    def interrupt(self, message: str) -> str:
        """
        人工介入检查点：存储中断信息，返回 id。
        调用方应轮询 get_latest_state() 等待用户回复。
        """
        import uuid
        int_id = str(uuid.uuid4())[:8]
        self.store("working", {
            "type": "interrupt",
            "id": int_id,
            "message": message,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }, tags=["interrupt"], importance=5.0)
        return int_id

    def get_latest_state(self) -> Dict:
        """返回最近一轮的 working 状态，包含用户反馈"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, content, tags, created_at FROM memories
                    WHERE tier = 'working'
                    ORDER BY created_at DESC LIMIT 20
                """)
                rows = cursor.fetchall()
                result = {"_interrupt": None, "user_feedbacks": []}
                for row in rows:
                    content = json.loads(row[1]) if isinstance(row[1], str) else row[1]
                    # 最新未处理的中断
                    if content.get("type") == "interrupt" and content.get("status") == "pending" \
                            and result["_interrupt"] is None:
                        result["_interrupt"] = content
                    # 用户反馈
                    if content.get("type") == "user_feedback":
                        result["user_feedbacks"].append(content)
                return result

    def resolve_interrupt(self, int_id: str, action: str = "approve"):
        """
        标记中断已处理（approve/reject）。
        Bot 收到 /approve <id> 或 /reject <id> 后调用；
        自主循环处理完也可自己调，防止中断记录残留导致重复挂起。
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT id, content FROM memories WHERE tier='working'")
                for mid, content_str in cursor.fetchall():
                    content = json.loads(content_str) if isinstance(content_str, str) else content_str
                    if content.get("type") == "interrupt" and content.get("id") == int_id:
                        content["status"] = "resolved"
                        content["resolved_by"] = action
                        conn.execute("UPDATE memories SET content=? WHERE id=?",
                                     (json.dumps(content, ensure_ascii=False), mid))
                        break


# 全局实例工厂
def create_memory(base_path: Path) -> TieredMemory:
    return TieredMemory(base_path)