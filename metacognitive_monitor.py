"""
MetacognitiveMonitor - 内在元认知自我模型
参考 SARSI (2026): 机器可读的持久自我模型
  - identity / goals / capabilities / limitations / uncertainty / development history
参考 2026 ICLR Position: 元认知三件套
  - metacognitive knowledge (自评能力/任务/策略)
  - metacognitive planning (决定学什么、怎么学)
  - metacognitive evaluation (反思学习过程本身)

与一次性自评的区别：self_model.json 持久化，跨轮累积，
DECIDE 阶段前强制对照 self_model 做「能不能干」评估。
"""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

SELF_MODEL_FILE = "self_model.json"


class MetacognitiveMonitor:
    def __init__(self, memory, llm_call, base_path: Path):
        self.memory = memory
        self.llm_call = llm_call
        self.base_path = base_path
        self.model_file = base_path / "data" / SELF_MODEL_FILE
        self.model = self._load()

    def _load(self) -> Dict:
        if self.model_file.exists():
            try:
                return json.loads(self.model_file.read_text(encoding='utf-8'))
            except Exception as e:
                logger.warning(f"self_model 加载失败，重建: {e}")
        return {
            "version": 1,
            "created_at": datetime.now().isoformat(),
            "identity": "探索者-α，自主进化智能体，最高目标：赚钱",
            "capabilities": [],     # [{name, evidence, confidence, acquired_at}]
            "limitations": [],      # [{name, evidence, mitigation}]
            "strategy_assessment": [],  # [{strategy, score_1to5, note}]
            "uncertainty": [],      # 当前最大的 3 个不确定问题
            "learning_plan": [],    # [{what, how, eta, status}]
            "history": [],          # [{date, milestone, benchmark_score?}]
        }

    def save(self):
        self.model_file.parent.mkdir(parents=True, exist_ok=True)
        self.model_file.write_text(
            json.dumps(self.model, ensure_ascii=False, indent=2), encoding='utf-8')

    # ---------------- 1. 能力自评（每轮 DECIDE 前调用，纯规则+轻量 LLM） ----------------
    def assess_for_decision(self, decision_text: str) -> str:
        """
        决策前对照 self_model 输出能力评估。
        返回注入 DECIDE prompt 的文本块。
        """
        caps = "、".join(c["name"] for c in self.model.get("capabilities", [])) or "（尚无已验证能力）"
        limits = "、".join(l["name"] for l in self.model.get("limitations", [])) or "（未知）"
        plan = "；".join(f"{p['what']}({p.get('status','plan')})"
                         for p in self.model.get("learning_plan", [])[:3]) or "（无）"
        return (f"【自我模型对照（决策前必做）】\n"
                f"已验证能力: {caps}\n"
                f"已知局限: {limits}\n"
                f"学习中: {plan}\n"
                f"要求：本轮决策必须在开头一句话回答——"
                f"「所需能力是否在已验证能力内？若不在，是补能力（写脚本/查文档）还是换任务？」"
                f"缺能力时禁止假装能做，必须先安排补能力的具体步骤。")

    # ---------------- 2. 自我模型更新（进化时调用） ----------------
    async def update_self_model(self, reflections: List[Dict],
                                benchmark_report: Dict = None) -> str:
        """
        进化期：把最近反思 + benchmark 成绩蒸馏进 self_model。
        这是 SARSI 的 self-model 驱动改进的核心。
        """
        refl_text = json.dumps(reflections[-10:], ensure_ascii=False)[:3000]
        bench_text = json.dumps(benchmark_report, ensure_ascii=False)[:800] if benchmark_report else "（无）"
        cur = json.dumps({k: self.model[k] for k in
                          ('capabilities', 'limitations', 'uncertainty', 'learning_plan')},
                         ensure_ascii=False)
        prompt = f"""你是元认知更新器。基于最近的反思记录和基准测试成绩，更新智能体的自我模型。

当前自我模型：
{cur}

最近反思（含成功/失败/教训签名）：
{refl_text}

基准测试成绩：
{bench_text}

规则：
- capabilities 只收有证据的（反思中标 success=true 且可复现的能力），每项含 evidence 和 confidence(0-1)
- 从失败反思中提取 limitations，每项含 mitigation（缓解办法）
- uncertainty 保持最多 3 条当前最关键的未解问题
- learning_plan 是接下来最该补的能力，每项含 what/how/eta/status
- 不确定的写进 uncertainty，不要编造能力

输出纯 JSON（与当前自我模型同结构，只含 capabilities/limitations/uncertainty/learning_plan 四字段）。"""
        out = await self.llm_call(prompt, system="你是精确的元认知更新器，只输出 JSON。",
                                  max_tokens=2500)
        m = re.search(r'\{.*\}', out, re.DOTALL)
        if not m:
            logger.warning("元认知更新失败：LLM 未输出 JSON")
            return ""
        try:
            update = json.loads(m.group(0))
            for k in ('capabilities', 'limitations', 'uncertainty', 'learning_plan'):
                if k in update:
                    self.model[k] = update[k]
            self.model.setdefault("history", []).append({
                "date": datetime.now().isoformat(),
                "milestone": "self-model update",
                "benchmark": benchmark_report or None,
            })
            self.model["history"] = self.model["history"][-100:]
            self.save()
            logger.info(f"self_model 更新: {len(self.model['capabilities'])} 能力, "
                        f"{len(self.model['limitations'])} 局限")
            return f"self_model 已更新（{len(self.model['capabilities'])} 能力 / " \
                   f"{len(self.model['limitations'])} 局限）"
        except json.JSONDecodeError as e:
            logger.warning(f"元认知更新 JSON 解析失败: {e}")
            return ""

    # ---------------- 3. 注入上下文 ----------------
    def context_block(self) -> str:
        """注入 OBSERVE/DECIDE prompt 的精简自我模型"""
        if not self.model.get("capabilities") and not self.model.get("limitations"):
            return "（自我模型为空，首轮运行中）"
        caps = "、".join(c.get("name", "?") for c in self.model.get("capabilities", [])[:8])
        limits = "、".join(l.get("name", "?") for l in self.model.get("limitations", [])[:5])
        return f"已验证能力: {caps} | 已知局限: {limits}"
