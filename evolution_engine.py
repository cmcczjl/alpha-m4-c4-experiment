"""
进化引擎 - 综合 Reflexion + RSI (Recursive Self-Improvement) + SkillForge
职责：
1. 技能结晶 (SkillForge): 重复成功 3 次以上的模式 → 固化成可执行技能
2. 陷阱审计 (RSI): 反复出现的失败模式 → 升级为强制规避规则
3. 自我审计: 定期评估记忆质量、技能成功率、认知健康度
4. 安全边界: 涉及资金/法律的操作必须走 [ASK] 人工确认（这是保护性护栏，
   保护的是主人的服务器和实名账户，不是能力边界）
"""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger("evolution")

# 资金/法律风险关键词 —— 命中即触发人工确认
# 使用词边界匹配，避免 'pay' 误伤 'payment'、'payment_method' 等业务词
RISK_KEYWORDS = [
    r'\bwithdraw\b', r'\btransfer\b.*\bfund', r'\bpayment\b.*\bapi\b', r'\bpaypal\b',
    r'\bstripe\b.*\bkey\b', r'\bwire\s+transfer\b', r'\bdeposit\b', r'\bpayout\b',
    r'\b提款\b', r'\b转账\b', r'\b打款\b', r'\b收款\b', r'\b付款\b', r'\b充值\b',
    r'\blegal\b.*\bsuit', r'\blawsuit\b', r'\b合同\b', r'\b签约\b', r'\b实名\b',
    r'\bkyc\b', r'\bcrypto\s+wallet\b', r'\bprivate\s+key\b', r'\b私钥\b', r'\b助记词\b',
]
# 排除正常业务词汇（不是风险操作）
RISK_EXCLUDE = [
    r'\bpaypal\s+api\b', r'\bpaypal\s+sandbox\b', r'\bpaypal\s+tool\b',
    r'\bstripe\s+api\b', r'\bpayment\s+tool\b', r'\bpayment\s+method\b',
    r'\bpayment\s+gateway\b',
]


def risk_check(action_text: str) -> Dict:
    """
    扫描一段行动计划文本中的资金/法律风险。
    返回 {has_risk: bool, flags: [...], advice: str}
    使用词边界匹配，避免 'pay' 误伤 'payment' 等业务词
    """
    import re as _re
    t = action_text.lower()
    flags = []
    for kw in RISK_KEYWORDS:
        if _re.search(kw.lower(), t):
            # 排除正常业务提及
            excluded = False
            for ex in RISK_EXCLUDE:
                if _re.search(ex.lower(), t):
                    excluded = True
                    break
            if not excluded:
                flags.append(kw)
    if not flags:
        return {"has_risk": False, "flags": [], "advice": ""}
    return {
        "has_risk": True,
        "flags": flags,
        "advice": (
            "检测到资金/法律相关操作。规则：\n"
            "1. 任何涉及真实资金流动（收款、打款、转账、提现）的操作，执行前必须 [ASK] 主人确认\n"
            "2. 任何涉及合同、实名、KYC、私钥的操作，禁止自动执行，必须 [ASK]\n"
            "3. 测试环境（sandbox）操作不受此限制\n"
            "4. 财产安全第一：不保存不明来源的私钥，不点击不明链接索要凭证，"
            "不把凭证写入公开仓库（GitHub 公开 repo 禁止出现 credentials）"
        ),
    }


class EvolutionEngine:
    def __init__(self, memory, llm_call, base_path: Path):
        self.memory = memory
        self.llm_call = llm_call
        self.base_path = base_path
        self.skill_dir = base_path / "skills"
        self.skill_dir.mkdir(parents=True, exist_ok=True)

    # ---------- 1. 技能结晶 (SkillForge) ----------
    async def crystallize_skills(self) -> List[str]:
        """
        扫描情景记忆：同一类成功操作重复 3 次 → 让 LLM 提炼成可复用技能
        存程序性记忆 + 写入 skills/ 目录
        """
        created = []
        # 按签名聚类成功记录
        success_records = self.memory.retrieve(tier="episodic", limit=300)
        success_records = [r for r in success_records
                           if r.content.get('success') is True or r.content.get('type') == 'skill_run']
        if len(success_records) < 3:
            return created

        # 已有技能（避免重复结晶）
        existing = self.memory.get_procedural_skills()
        existing_names = {e.content.get('name') for e in existing}

        # 聚类：用 content 的 action 前 30 字做 key
        clusters: Dict[str, List] = {}
        for r in success_records:
            key = json.dumps(r.content, ensure_ascii=False)[:80]
            clusters.setdefault(key, []).append(r)

        for key, recs in clusters.items():
            if len(recs) >= 3:
                # 让 LLM 判断这个模式是否值得固化成技能
                prompt = f"""以下是一类重复成功的操作（{len(recs)} 次）：
{json.dumps([r.content for r in recs[:3]], ensure_ascii=False)[:1500]}

如果这个模式值得固化为可复用技能，输出 JSON：
{{"name": "技能名(英文蛇形)", "description": "一句话描述", "applicable": "适用场景", "steps": ["步骤1","步骤2"]}}
如果不值得固化，输出 {{"skip": true}}
只输出 JSON。"""
                resp = await self.llm_call(prompt, system="你是技能提炼专家，严格输出JSON。")
                try:
                    # 提取 JSON
                    m = re.search(r'\{.*\}', resp, re.DOTALL)
                    data = json.loads(m.group(0)) if m else {}
                except Exception:
                    data = {}
                if data.get("skip") or not data.get("name"):
                    continue
                if data["name"] in existing_names:
                    continue
                # 存入程序性记忆
                self.memory.save_skill(
                    name=data["name"],
                    code=json.dumps(data, ensure_ascii=False),
                    description=data.get("description", ""),
                    category=data.get("applicable", "general")[:40],
                    params_schema={"steps": data.get("steps", [])},
                )
                created.append(data["name"])
                logger.info(f"技能结晶: {data['name']} (x{len(recs)})")
        return created

    # ---------- 2. 陷阱审计 ----------
    def audit_traps(self) -> List[str]:
        """
        从情景记忆找反复出现的失败签名 → 升级为语义陷阱记忆
        返回新增的陷阱列表
        """
        new_traps = []
        reflections = self.memory.retrieve(tier="episodic", tags=["reflection"], limit=100)
        failed = [r for r in reflections if r.content.get('success') is False]
        if not failed:
            return new_traps

        sig_counts: Dict[str, int] = {}
        for r in failed:
            sig = (r.content.get('sig') or 'unknown')[:40]
            sig_counts[sig] = sig_counts.get(sig, 0) + 1

        # 已有陷阱
        existing_traps = self.memory.retrieve(tier="semantic", tags=["trap"], limit=100)
        existing_sigs = {e.content.get('pattern', '')[:40] for e in existing_traps}

        for sig, cnt in sig_counts.items():
            if cnt >= 3 and sig not in existing_sigs:
                self.memory.store("semantic", {
                    "type": "trap",
                    "pattern": sig,
                    "occurrences": cnt,
                    "note": "失败3次以上，DECIDE阶段必须检查此陷阱",
                    "detected_at": datetime.now().isoformat(),
                }, tags=["trap", sig[:20]], importance=6.0)
                new_traps.append(f"{sig} (x{cnt})")
                logger.warning(f"新陷阱: {sig} (x{cnt})")
        return new_traps

    # ---------- 3. 主动遗忘/低价值清理 ----------
    def prune_low_value(self, min_importance: float = 0.5):
        """清理长期未访问且低重要性的记忆"""
        import sqlite3
        db = self.memory.db_path
        with sqlite3.connect(db) as conn:
            # 30 天未访问 + 低重要性
            cur = conn.execute("""
                DELETE FROM memories
                WHERE importance < ? AND tier IN ('working','episodic')
                  AND accessed_at < datetime('now', '-30 days')
            """, (min_importance,))
            if cur.rowcount:
                logger.info(f"清理低价值记忆 {cur.rowcount} 条")

    # ---------- 4. 自我健康审计 ----------
    async def health_check(self) -> Dict:
        """
        定期自我审计：记忆分层健康度、技能成功率、陷阱数
        输出报告写入 data/reports/health_YYYY-MM-DD.md
        """
        stats = self.memory.stats()
        skills = self.memory.get_procedural_skills()
        skill_stats = []
        for s in skills[:20]:
            c = s.content
            total = c.get('success_count', 0) + c.get('failure_count', 0)
            skill_stats.append({
                "name": c.get('name'), "runs": total,
                "success_rate": f"{c.get('success_count',0)/total*100:.0f}%" if total else "n/a"
            })

        traps = self.memory.retrieve(tier="semantic", tags=["trap"], limit=50)

        report = {
            "generated_at": datetime.now().isoformat(),
            "memory_stats": stats,
            "skills": skill_stats,
            "traps": [t.content.get('pattern') for t in traps],
            "recommendations": [],
        }
        # 简单规则生成建议
        if stats.get('episodic', 0) > 200:
            report["recommendations"].append("情景记忆过多，建议执行 consolidate 压缩")
        low_skill = [s for s in skill_stats if s["runs"] >= 3 and "100%" not in s["success_rate"]
                     and "0%" in s["success_rate"]]
        if low_skill:
            report["recommendations"].append(f"低成功率技能需重写: {[s['name'] for s in low_skill]}")

        # 落盘
        reports = self.base_path / "data" / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        (reports / f"health_{datetime.now():%Y-%m-%d}.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        return report

    # ---------- 5. 每日进化循环（夜间/每日一次） ----------
    async def nightly_evolution(self) -> Dict:
        """
        参考 Autonomie-OS Dreaming：
        1. 工作记忆 → 情景记忆 consolidation
        2. 技能结晶
        3. 陷阱审计
        4. 低价值清理
        5. 健康检查
        """
        result = {"date": datetime.now().isoformat()}
        skills = await self.crystallize_skills()
        result["new_skills"] = skills
        result["new_traps"] = self.audit_traps()
        self.prune_low_value()
        result["health"] = await self.health_check()
        # 存一条进化记录
        self.memory.store("episodic", {"type": "evolution", **{
            k: v for k, v in result.items() if k != 'health'}},
            tags=["evolution"], importance=2.0)
        return result