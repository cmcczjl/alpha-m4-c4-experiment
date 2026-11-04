"""
AGI 智能体 - 自主进化赚钱代理
从零开始，自主发现、验证、执行、进化
"""

import os
import sys
import json
import sqlite3
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from contextlib import contextmanager

import yaml
import httpx
from openai import AsyncOpenAI

# 配置
CONFIG_PATH = Path(__file__).parent / "config.yaml"

def load_config() -> dict:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

CONFIG = load_config()

# 日志
logging.basicConfig(
    level=getattr(logging, CONFIG['agent']['log']['level']),
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(f"data/{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== 记忆系统 ====================

@dataclass
class MemoryItem:
    """记忆单元"""
    id: str
    type: str  # scene/semantic/procedural
    content: str
    tags: list[str]
    confidence: float
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    def to_dict(self):
        d = asdict(self)
        d['created_at'] = self.created_at.isoformat()
        if self.expires_at:
            d['expires_at'] = self.expires_at.isoformat()
        return d

class MemorySystem:
    """
    三层记忆系统
    - 情景记忆：短期会话（L2缓存）
    - 语义记忆：长期知识（向量库）
    - 程序记忆：技能规则（可执行）
    """
    
    def __init__(self, db_path: str, journal_path: str, lessons_path: str):
        self.db_path = db_path
        self.journal_path = Path(journal_path)
        self.lessons_path = Path(lessons_path)
        self.db = None
        self._init_db()
        
    def _init_db(self):
        """初始化数据库"""
        self.db = sqlite3.connect(self.db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        cursor = self.db.cursor()
        
        # 情景记忆
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT,
                confidence REAL DEFAULT 0.5,
                created_at TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        
        # 决策日志
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY,
                timestamp TIMESTAMP,
                context TEXT,
                action TEXT,
                result TEXT,
                notes TEXT
            )
        ''')
        
        # 假设库
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hypotheses (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                trigger_conditions TEXT,
                confidence REAL DEFAULT 0.5,
                test_count INTEGER DEFAULT 0,
                win_count INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0.0,
                status TEXT DEFAULT 'testing',
                created_at TIMESTAMP,
                last_tested TIMESTAMP
            )
        ''')
        
        # 测试结果
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id TEXT PRIMARY KEY,
                hypothesis_id TEXT,
                test_type TEXT,
                entry_price REAL,
                exit_price REAL,
                pnl REAL,
                hold_time REAL,
                market_context TEXT,
                decision_reason TEXT,
                timestamp TIMESTAMP
            )
        ''')
        
        # 知识索引
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_index (
                id TEXT PRIMARY KEY,
                topic TEXT,
                summary TEXT,
                file_path TEXT,
                created_at TIMESTAMP
            )
        ''')
        
        self.db.commit()
        
        # 创建目录
        self.journal_path.mkdir(parents=True, exist_ok=True)
        
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
            
    def save_decision(self, context: dict, action: str, result: dict, notes: str = ""):
        """记录决策"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            decision_id = f"dec_{datetime.now().timestamp():.0f}"
            cursor.execute('''
                INSERT INTO decisions (id, timestamp, context, action, result, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                decision_id,
                datetime.now().isoformat(),
                json.dumps(context, ensure_ascii=False),
                action,
                json.dumps(result, ensure_ascii=False),
                notes
            ))
            conn.commit()
        return decision_id
    
    def save_hypothesis(self, name: str, description: str, trigger_conditions: dict) -> str:
        """保存假设"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            hyp_id = f"hyp_{datetime.now().timestamp():.0f}"
            cursor.execute('''
                INSERT INTO hypotheses (id, name, description, trigger_conditions, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                hyp_id, name, description, 
                json.dumps(trigger_conditions, ensure_ascii=False),
                datetime.now().isoformat()
            ))
            conn.commit()
        return hyp_id
    
    def record_test_result(self, hypothesis_id: str, result: dict):
        """记录测试结果"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            test_id = f"test_{datetime.now().timestamp():.0f}"
            cursor.execute('''
                INSERT INTO test_results (id, hypothesis_id, test_type, entry_price, exit_price, pnl, hold_time, market_context, decision_reason, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                test_id, hypothesis_id, result.get('type', 'live'),
                result.get('entry_price', 0), result.get('exit_price', 0),
                result.get('pnl', 0), result.get('hold_time', 0),
                json.dumps(result.get('market', {}), ensure_ascii=False),
                result.get('reason', ''),
                datetime.now().isoformat()
            ))
            conn.commit()
            
            # 更新假设
            wins = 1 if result.get('pnl', 0) > 0 else 0
            cursor.execute('''
                UPDATE hypotheses SET
                    test_count = test_count + 1,
                    win_count = win_count + ?,
                    total_pnl = total_pnl + ?,
                    last_tested = ?,
                    confidence = CASE WHEN test_count + 1 > 0 THEN CAST(win_count + ? AS REAL) / (test_count + 1) ELSE 0.5 END
                WHERE id = ?
            ''', (wins, result.get('pnl', 0), datetime.now().isoformat(), wins, hypothesis_id))
            conn.commit()
            
    def get_pending_hypotheses(self, max_tests: int = 10, min_confidence: float = 0.3) -> list:
        """获取待测试假设"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM hypotheses 
                WHERE test_count < ? 
                AND confidence >= ?
                AND status = 'testing'
                ORDER BY confidence DESC, test_count ASC
                LIMIT 10
            ''', (max_tests, min_confidence))
            return [dict(row) for row in cursor.fetchall()]
            
    def get_validated_hypotheses(self, min_win_rate: float = 0.55, min_tests: int = 5) -> list:
        """获取已验证假设"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM hypotheses 
                WHERE test_count >= ?
                AND (CAST(win_count AS REAL) / test_count) >= ?
                AND status = 'validated'
            ''', (min_tests, min_win_rate))
            return [dict(row) for row in cursor.fetchall()]
            
    def save_journal_entry(self, day: str, entries: list[dict]):
        """保存每日日记"""
        journal_file = self.journal_path / f"{day}.md"
        with open(journal_file, 'w', encoding='utf-8') as f:
            f.write(f"# {day} 决策日志\n\n")
            for entry in entries:
                f.write(f"## {entry.get('time', 'Unknown')}\n\n")
                f.write(f"**决策**: {entry.get('decision', 'N/A')}\n\n")
                f.write(f"**结果**: {entry.get('result', 'N/A')}\n\n")
                f.write(f"**PnL**: {entry.get('pnl', 'N/A')}\n\n")
                f.write("---\n\n")
        logger.info(f"Journal saved: {journal_file}")
        
    def save_lessons(self, lessons: list[dict]):
        """保存失败教训"""
        with open(self.lessons_path, 'w', encoding='utf-8') as f:
            json.dump({
                'updated_at': datetime.now().isoformat(),
                'lessons': lessons
            }, f, ensure_ascii=False, indent=2)
        logger.info(f"Lessons saved: {len(lessons)} entries")
        
    def load_lessons(self) -> list:
        """加载失败教训"""
        if self.lessons_path.exists():
            with open(self.lessons_path, 'r', encoding='utf-8') as f:
                return json.load(f).get('lessons', [])
        return []
        
    def check_lesson_conflict(self, action_desc: str) -> Optional[str]:
        """检查是否违反已知教训"""
        lessons = self.load_lessons()
        for lesson in lessons:
            # 简单关键词匹配（实际应用用向量检索）
            if any(keyword in action_desc for keyword in lesson.get('keywords', [])):
                return f"警告：此操作违反已知教训 - {lesson.get('reason', '')}"
        return None
