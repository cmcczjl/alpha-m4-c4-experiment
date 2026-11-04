"""
ConstitutionEngine - 宪法式规则沉淀
参考 OmniReflect (2026): 把碎片反思蒸馏为分类宪法（rule book）
参考 HMED (2026.10): 被拒绝/失败的修改方向也要记录（负面经验同样有价值）

宪法 = 从情景记忆中提炼的紧凑指导原则，注入每一轮 prompt，
定期（每 8 轮）重蒸，控制冗余（> 30 条时合并同类）。
分类：
  - risk_avoidance   风险规避（资金/法律/凭证）
  - dev_practices    开发规范（写码/测试/验证）
  - strategy         策略偏好（方向选择/探索节奏）
  - tools_env        工具与环境事实（API 位置/命令限制）
  - communication    沟通与汇报规范
"""
import json
import re
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

CONSTITUTION_FILE = "constitution.md"


class ConstitutionEngine:
    def __init__(self, memory, llm_call, base_path: Path):
        self.memory = memory
        self.llm_call = llm_call
        self.base_path = base_path
        self.path = base_path / "data" / CONSTITUTION_FILE

    def load(self) -> str:
        if self.path.exists():
            return self.path.read_text(encoding='utf-8')
        return "# 探索者-α 宪法\n\n（尚未蒸馏，进化期自动生成）\n"

    def context_block(self, max_chars: int = 1800) -> str:
        text = self.load().strip()
        if len(text) > max_chars:
            text = text[:max_chars] + "\n…(宪法过长，截断)"
        return text or "（宪法为空）"

    async def distill(self, force: bool = False) -> str:
        """
        进化期：把最近反思（含失败）蒸馏/合并进宪法。
        - 成功经验 → 正向规则
        - 失败经验 → "禁止 X" 规则（HMED：负面修改同样入宪）
        - 已有宪法作为输入，做增量合并，不推倒重来
        """
        recent = self.memory.retrieve(tier="episodic", tags=["reflection"], limit=30)
        if not recent and not force:
            return ""
        # 按 sig 去重统计
        sig_groups = {}
        for r in recent:
            sig = r.content.get("sig", "unknown")[:40]
            g = sig_groups.setdefault(sig, {"count": 0, "success": 0, "fail": 0,
                                            "sample": ""})
            g["count"] += 1
            if r.content.get("success"):
                g["success"] += 1
            else:
                g["fail"] += 1
            if not g["sample"]:
                g["sample"] = (r.content.get("reflection") or "")[:150]
        groups_json = json.dumps(
            [{"sig": k, **v} for k, v in sig_groups.items()], ensure_ascii=False)[:3500]
        cur = self.load()
        prompt = f"""你是宪法蒸馏器。把智能体的经验教训整理成一份紧凑的「宪法」规则书。

当前宪法：
{cur[:2500]}

近期经验分组（sig=教训签名，含成功/失败次数）：
{groups_json}

规则：
1. 分类组织：## 风险规避 / ## 开发规范 / ## 策略 / ## 工具与环境 / ## 沟通汇报
2. 每条规则一行，以 - 开头，具体可执行（"X 必须 Y" 或 "禁止 Z"），不写空话
3. 失败 sig → 写成"禁止/必须避免"规则；成功 sig → 写成"遵循"规则
4. 与当前宪法合并：保留仍然有效的旧规则，同类规则合并，重复的删除
5. 总长度控制在 1200 字以内（宪法要能注入每轮 prompt）
6. 顶部保留 # 探索者-α 宪法 和一行 最后更新: 日期

直接输出完整宪法 Markdown 文本。"""
        out = await self.llm_call(prompt, system="你是宪法蒸馏器，只输出 Markdown。",
                                  max_tokens=2500)
        if not out or out.startswith("[错误]"):
            logger.warning("宪法蒸馏失败（LLM 错误）")
            return ""
        out = out.strip()
        if not out.startswith("#"):
            out = "# 探索者-α 宪法\n" + out
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(out + f"\n<!-- distilled at {datetime.now().isoformat()} -->\n",
                             encoding='utf-8')
        logger.info(f"宪法已蒸馏: {len(out)} 字符")
        return f"宪法已蒸馏（{len(out)} 字符）"
