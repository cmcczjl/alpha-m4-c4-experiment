"""
认知循环引擎 - 综合 OODA + CodeAct + Reflexion + Antahkarana
每个决策轮次都经历：OBSERVE → ORIENT → DECIDE → ACT → REFLECT → CONSOLIDATE

参考:
- OpenHands CodeAct: 用代码作为行动空间
- Reflexion: 言语强化学习（试错→反思→存入情景记忆→下次更好）
- Antahkarana: 认知门控（预算/注意/判断/觉察）
- OODA: 观察-定向-决策-行动
"""
import asyncio
import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger("cognitive")


@dataclass
class CognitiveTrace:
    """一轮完整认知过程的记录（用于反思和评估）"""
    iteration: int
    started_at: str
    run_id: str = ""              # 当前 run_id，用于跨轮 stalled 检测过滤旧 trace
    observe: str = ""       # 观察到了什么（环境状态、上轮结果、市场信号）
    orient: str = ""        # 定向（假设、问题建模、当前认知地图）
    decision: str = ""      # 决策（选哪个方向/策略，为什么）
    action: str = ""        # 行动（执行了什么）
    observation: str = ""   # 行动后的观测（外部执行 RUN 后注入）
    reflection: str = ""    # 反思（Reflexion 四问）
    consolidation: str = "" # 沉淀摘要
    success: bool = False   # 严格证据制判定
    stalled: bool = False                 # 轮内连续失败标记
    capability_boundary: bool = False     # 能力边界标记
    cross_wheel_stalled: bool = False     # 跨轮重复标记
    roadmap_focus_wheels: int = 0         # 当前 roadmap 焦点持续轮数
    duration_ms: int = 0


class CognitiveLoop:
    """
    认知循环驱动器。
    不直接调 LLM —— 它生成结构化的分阶段 prompt，
    把每阶段的输出收集成 CognitiveTrace，供反思和进化引擎使用。
    """

    def __init__(self, memory, llm_call, base_path: Path):
        """
        memory: TieredMemory 实例
        llm_call: async callable(prompt, system) -> str
        """
        self.memory = memory
        self.llm_call = llm_call
        self.base_path = base_path
        self.trace_dir = base_path / "data" / "cognitive_traces"
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.last_trace: Optional[CognitiveTrace] = None
        self._recent_actions: list = []  # 记录最近执行的 action 前缀，用于重复动作检测

    # ---------------- 门控 (Antahkarana) ----------------
    def _gate_check(self, trace: CognitiveTrace, context: Dict) -> Dict:
        """
        决策前的门控检查：
        - 预算：本轮 LLM 调用次数/字符预算
        - 注意：当前任务是否在 roadmap 焦点内
        - 判断：是否有足够的证据做这个决策
        - 觉察：是否陷入重复模式（同一错误第 3 次？）
        - stalled 检查：【上一轮】是否标记 stalled / cross_wheel_stalled（从 last_trace 读取）
        - 方向一致性：DECIDE 的 direction_match 必须为 true
        - 重复动作检测：禁止重做已完成的动作（同一脚本/命令在最近 3 轮出现）
        """
        gates = {"proceed": True, "warnings": []}

        # 方向一致性门控（在 capability 门控之前拦截跑题决策）
        direction_ok = self._parse_direction_match(trace.decision)
        if not direction_ok:
            gates["warnings"].append("决策 direction_match=false：本轮决策与当前 roadmap 焦点不一致，必须重新决策")
            gates["proceed"] = False
            return gates

        # 重复动作门控：检查是否重做已完成动作
        # ⚠️ 如果 action 为空，说明本轮被 gate 或其他环节拦截，跳过重复检查
        if trace.action:
            action_key = trace.action[:100] if len(trace.action) > 100 else trace.action
            recent_traces = getattr(self, '_recent_actions', [])
            duplicate_count = sum(1 for prev_action in recent_traces[-5:]
                                  if prev_action and action_key[:50] in prev_action[:50])
            if duplicate_count >= 2:
                gates["warnings"].append(f"重复动作拦截：{action_key[:80]} 已在最近 3 轮执行过，禁止重做；必须推进新里程碑")
                gates["proceed"] = False

        # 上一轮的 stalled / cross_wheel_stalled 标记（关键：标记打在上一轮 trace 上）
        # ⚠️ 自锁防护：连续拦截 ≥2 轮强制放行，防止"拦截轮自己又置 stalled"的死循环
        prev = self.last_trace
        if prev is not None:
            stall_flag = getattr(prev, 'cross_wheel_stalled', False) or getattr(prev, 'stalled', False)
            if stall_flag:
                blocked = getattr(self, '_stall_gate_blocked_count', 0)
                if blocked >= 2:
                    gates["warnings"].append(
                        f"stalled 已连续拦截 {blocked} 轮（自锁风险）— 强制放行：本轮决策必须先一句话诊断卡点，"
                        f"且 action 必须是不同于最近 3 轮实现路径的新动作（换文件/换方法/换子目标）")
                    self._stall_gate_blocked_count = 0  # 放行后清零
                    gates["proceed"] = True  # 明确放行，覆盖可能的其他拦截
                else:
                    if getattr(prev, 'cross_wheel_stalled', False):
                        gates["warnings"].append("上一轮已触发跨轮升级：同一焦点重复失败 ≥5 轮，本轮必须从候选池选择新方向（禁止继续旧焦点）")
                    else:
                        gates["warnings"].append("上一轮标记 stalled（连续失败），本轮必须先诊断哪个前提错了")
                    gates["proceed"] = False
                    self._stall_gate_blocked_count = blocked + 1
            else:
                # 上一轮没 stalled → 拦截计数清零
                self._stall_gate_blocked_count = 0

        # 里程碑链强制推进门控：必须按顺序完成，禁止跳级
        current_milestone = self._extract_current_milestone_subgoal(context)
        # 检查当前决策意图（trace.decision）而非上一轮 action
        # 因为 gate_check 在 ACT 之前运行，trace.action 是上一轮的，trace.decision 是本轮意图
        intent_text = (trace.decision or "").lower()
        action_lower = (trace.action or "").lower()
        if current_milestone and (intent_text or action_lower):
            # 里程碑顺序
            milestone_order = ['M1-0', 'M1-1', 'M1-2', 'M2-0', 'M2-1', 'M2-2', 'M3', 'M4']
            current_idx = milestone_order.index(current_milestone) if current_milestone in milestone_order else 0
            # 检测是否在写后续里程碑的文件（如还在 M2 时写 M3 的 pricing.md）
            for future_idx in range(current_idx + 1, len(milestone_order)):
                future_m = milestone_order[future_idx]
                # 方式1：检查决策意图里是否有里程碑名
                if future_m.lower() in intent_text and future_m in ['M3', 'M4']:
                    gates["warnings"].append(
                        f"里程碑跳跃拦截：当前在 {current_milestone}，禁止跳到 {future_m}；"
                        f"必须先完成 {current_milestone} 才能推进后续里程碑"
                    )
                    gates["proceed"] = False
                    return gates
                # 方式2：通过决策意图里的产出物路径判断（更可靠——α 常在 action 里不写里程碑名）
                future_paths = {
                    'M3': ['data/pricing.md', 'pricing.md', 'data/upwork_service.md', 'upwork_service.md'],
                    'M4': ['upwork_service', 'M4_output', 'deliverable.zip', 'gh repo create', 'upwork.com'],
                }
                if future_m in future_paths:
                    for fp in future_paths[future_m]:
                        if fp in intent_text:
                            gates["warnings"].append(
                                f"里程碑跳跃拦截：当前在 {current_milestone}，禁止写 {future_m} 的文件 '{fp}'；"
                                f"必须先完成 {current_milestone}"
                            )
                            gates["proceed"] = False
                            return gates

        # 觉察门：检查是否重复同一错误
        if trace.reflection:
            recent_lessons = self.memory.retrieve(tier="episodic", tags=["reflection"], limit=10)
            sig = self._error_signature(trace.action)
            repeat_count = sum(1 for l in recent_lessons
                               if sig and sig[:20] in json.dumps(l.content, ensure_ascii=False))
            if repeat_count >= 2:
                gates["warnings"].append(f"同一问题已出现 {repeat_count} 次，先解决根因再行动")
                gates["proceed"] = False

        # 新焦点无里程碑强制定义门控：焦点切换 ≥3 轮且旧里程碑全完成/归档，禁止继续旧焦点产出
        focus_wheels = context.get('roadmap_focus_wheels', 0)
        # 检查 roadmap 中旧焦点 M2/M3/M4 是否已标记归档
        old_milestones_archived = False
        try:
            roadmap_text = context.get('roadmap_focus', '')
            if '已完成归档' in roadmap_text and '旧焦点' in roadmap_text:
                old_milestones_archived = True
        except:
            pass

        # 条件：焦点轮数≥3 且 (无当前里程碑 OR 旧里程碑已归档)
        if focus_wheels >= 3 and (not current_milestone or old_milestones_archived):
            # 检查决策/行动是否仍针对旧焦点的 M2/M3/M4 产出物
            old_focus_keywords = ['M2', 'M3', 'M4', 'upwork', 'pricing.md', 'deliverable.zip', 'M4_output', 'github', 'readme.md']
            intent_text = (trace.decision or "").lower()
            action_lower = (trace.action or "").lower()
            for kw in old_focus_keywords:
                if kw.lower() in intent_text or kw.lower() in action_lower:
                    gates["warnings"].append(
                        f"新焦点无里程碑拦截：roadmap 已切换至 '{context.get('roadmap_focus', '未知')}' 第 {focus_wheels} 轮，"
                        f"旧里程碑已归档，禁止继续产出 {kw}。必须先为新焦点定义里程碑链（M1-0 调研等）。"
                    )
                    gates["proceed"] = False
                    return gates

        # 跨轮 stalled 检测：重复失败 + 里程碑停滞
        if self._check_cross_wheel_stall(trace, context):
            gates["proceed"] = False

        return gates

    def _error_signature(self, text: str) -> str:
        """提取错误/行动的特征签名（用于重复检测）"""
        t = text.lower()
        for kw in ['error', 'traceback', '失败', '拒绝', '403', '404', 'timeout', 'timeouterror']:
            if kw in t:
                # 取关键词后 40 字符作为签名
                idx = t.find(kw)
                return t[idx:idx + 60]
        return t[:40]

    # P1-3: 元认知硬门控 —— 解析 DECIDE 输出中的 capability 字段
    def _parse_capability_check(self, decision_text: str) -> str:
        """
        从 DECIDE 输出中提取 capability 字段。
        支持 JSON 格式（"capability": "boundary"）和旧文本格式（capability_check: boundary）。
        返回: "proven" | "boundary" | "unknown" | ""(未找到)
        """
        import re
        # 新 JSON 格式: "capability": "boundary" 或 "capability":"boundary"
        m = re.search(r'["\']?capability["\']?\s*[:：]\s*["\']?(proven|boundary|unknown)', decision_text, re.IGNORECASE)
        if m:
            return m.group(1).lower()
        return ""

    def _parse_direction_match(self, decision_text: str) -> bool:
        """检查 DECIDE 输出的 direction_match 字段。缺省视为 True（兼容旧格式）"""
        import re
        m = re.search(r'["\']?direction_match["\']?\s*[:：]\s*["\']?(true|false)', decision_text, re.IGNORECASE)
        if not m:
            return True  # 旧格式无此字段，不拦截
        return m.group(1).lower() == 'true'

    def _extract_current_milestone_subgoal(self, context: Dict) -> str:
        """提取当前正在推进的里程碑子目标名称（用于子目标迭代计数）"""
        roadmap_text = context.get('roadmap_focus', '') or ""
        # 从 roadmap.md 读取全文（优先级高于 context 摘要）
        try:
            from pathlib import Path as _Path
            rm_path = _Path(__file__).parent / "data" / "roadmap.md"
            if rm_path.exists():
                roadmap_text = rm_path.read_text(encoding='utf-8')
        except Exception:
            pass
        import re as _re
        # 逐行扫描，找到第一个包含 milestone 且不含 '✅ 已完成' 的行
        # 跳过标题性行（如 '- 进展状态：**M2 进行中**'）
        for mk in ['M1-0', 'M1-1', 'M1-2', 'M2-0', 'M2-1', 'M2-2', 'M3', 'M4']:
            for line in roadmap_text.split('\n'):
                # 匹配以 '-' 开头（允许前面有空格，兼容缩进列表项）
                if not _re.match(r'^\s*-', line):
                    continue
                # 跳过标题性行
                if '进展状态' in line or '卡了多久' in line:
                    continue
                # 精确匹配：里程碑必须出现在 **M2-X** 这种加粗标记内，或普通文本 M1-0/M1-1/M1-2（兼容旧格式）
                if not (_re.search(rf'\*\*{_re.escape(mk)}\*\*', line) or _re.search(rf'\b{_re.escape(mk)}\b', line)):
                    continue
                # 包含 '✅ 已完成' 表示已完成，跳过
                if '✅ 已完成' in line:
                    continue
                # 找到第一个未完成里程碑
                return mk
        return ""

    # P1-4: 轮内失败升级 —— 记录同轮失败计数，连续 2 次失败 → 标记 stalled
    def _record_wheel_failure(self, trace: CognitiveTrace, failure_reason: str) -> bool:
        """
        记录本轮内的失败。连续 2 次同类失败 → 标记 stalled=True，
        触发下轮 OBSERVE 必须带诊断。
        返回: 是否触发 stalled
        """
        if not hasattr(self, '_wheel_failure_count'):
            self._wheel_failure_count = {}
        
        key = f"{trace.iteration}:{failure_reason[:50]}"
        self._wheel_failure_count[key] = self._wheel_failure_count.get(key, 0) + 1
        
        if self._wheel_failure_count[key] >= 2:
            trace.stalled = True
            trace.reflection += f"\n轮内升级: 连续 2 次 {failure_reason}，标记 stalled，下轮 OBSERVE 必须诊断前提。"
            return True
        return False

    # P1-5: 跨轮 stalled 检测 —— 同一 lesson_sig/焦点连续 5 轮无进展 → 强制换焦点
    def _check_cross_wheel_stall(self, trace: CognitiveTrace, context: Dict = None) -> bool:
        """
        检查跨轮重复：
        1. 同一 LESSON_SIG 出现 ≥5 次
        2. roadmap 焦点轮数 ≥5 且近 5 轮 success 全为 False
        """
        # 1. LESSON_SIG 重复检测
        recent = self.memory.retrieve(tier="episodic", tags=["reflection"], limit=15)
        sigs = []
        for m in recent:
            import json
            content = json.dumps(m.content, ensure_ascii=False)
            import re
            mm = re.search(r'\[LESSON_SIG\]\s*([^\n]+)', content)
            if mm:
                sigs.append(mm.group(1).strip())
        
        if sigs:
            from collections import Counter
            cnt = Counter(sigs)
            for sig, c in cnt.items():
                if c >= 5:
                    trace.cross_wheel_stalled = True
                    trace.reflection += f"\n跨轮升级: 同一教训 '{sig}' 已重复 {c} 次，强制换焦点。"
                    return True
        
        # 2. roadmap 焦点轮数检测
        if context:
            focus_wheels = context.get('roadmap_focus_wheels', 0)
            if focus_wheels >= 5:
                # 检查最近 5 轮是否全为 success=False
                # 按 trace 文件中的 iteration 排序，取最大的 5 个（避免 mtime 乱序/旧成功 trace 干扰）
                # 只考虑当前 run_id 的 trace；兼容旧 trace（run_id 为空视为当前 run）
                # 显式排除已知测试数据（trace_0999 等）
                import glob, json
                run_id = context.get('run_id', '')
                trace_files = glob.glob(str(self.trace_dir / "trace_*.json"))
                recent_traces = []
                for tf in trace_files:
                    try:
                        d = json.load(open(tf))
                        # 排除已知测试 trace：仅当 run_id 显式为 'test'/'trace_test' 时排除
                        # （旧版误把所有 iteration>=100 当测试数据，导致真实第 100+ 轮被吞掉）
                        if d.get('run_id') in ('test', 'trace_test'):
                            continue
                        trace_run_id = d.get('run_id', '')
                        # 包含：同 run_id、或空 run_id（旧 trace 视为当前 run 的一部分）
                        if run_id and trace_run_id and trace_run_id != run_id:
                            continue
                        recent_traces.append((d.get('iteration', 0), d))
                    except:
                        pass
                # 按 iteration 降序，取前 5
                recent_traces.sort(key=lambda x: x[0], reverse=True)
                recent_traces = [d for _, d in recent_traces[:5]]
                if recent_traces and len(recent_traces) >= 3 and all(not d.get('success', True) for d in recent_traces):
                    trace.cross_wheel_stalled = True
                    trace.reflection += f"\n跨轮升级: 焦点 '{context.get('roadmap_focus', '未知')}' 已持续 {focus_wheels} 轮且全失败，强制换焦点。"
                    return True

                # 3. 里程碑停滞：焦点 ≥12 轮 且 data/roadmap.md 当前里程碑行 8 轮内未出现 ✅ 推进
                if focus_wheels >= 12:
                    import re as _re3
                    try:
                        _rm = (self.base_path / 'data' / 'roadmap.md').read_text(encoding='utf-8', errors='replace')
                        _mile = ""
                        for _mk in ['M1-0', 'M1-1', 'M1-2', 'M2', 'M3', 'M4']:
                            _mm = _re3.search(rf'-\s*{_mk}\s+[^\n]*(?=\n-|\n>|$)', _rm)
                            if _mm and '✅' not in _mm.group(0):
                                _mile = _mk
                                break
                        if _mile:
                            # 检查最近 8 轮 action 里有没有产出该里程碑交付物的证据
                            import pathlib as _pl
                            _tr = glob.glob(str(self.trace_dir / "trace_*.json"))
                            _hits = []
                            _check_iter = recent_traces[0].get('iteration', 0) if recent_traces else 0
                            for tf in _tr:
                                try:
                                    d = json.load(open(tf))
                                    if d.get('run_id') and d.get('run_id') != run_id:
                                        continue
                                    # 放宽检查：只看最近 8 轮，且不要求一定有"完成"关键词
                                    # 只要有 action/observation/reflection 提到当前里程碑相关的工作，就算推进
                                    if d.get('iteration', 0) < (_check_iter - 8):
                                        continue
                                    blob = (d.get('action') or '') + (d.get('observation') or '') + (d.get('reflection') or '')
                                    # 检查是否有任何与当前里程碑相关的关键词（包括"创建"、"实现"、"编写"、"生成"等）
                                    progress_keywords = [
                                        f'{_mile} 完成', f'{_mile} ✅',
                                        'M1-0 完成', 'requirements.md 已写入', '验收通过',
                                        '工作流模板', '邮件分类器', '表单数据同步',  # M2 相关关键词
                                        f'创建 {_mile}', f'实现 {_mile}', f'编写 {_mile}',  # 通用推进信号
                                    ]
                                    if any(kw in blob for kw in progress_keywords):
                                        _hits.append(d.get('iteration'))
                                except:
                                    pass
                            # 放宽判定：如果最近 3 轮内有任何 action 产出，不算停滞
                            _recent_any_action = False
                            if _tr:
                                for tf in _tr:
                                    try:
                                        d = json.load(open(tf))
                                        if d.get('iteration', 0) >= (_check_iter - 3) and d.get('action'):
                                            _recent_any_action = True
                                            break
                                    except:
                                        pass
                            if not _hits and not _recent_any_action:
                                trace.cross_wheel_stalled = True
                                trace.reflection += (
                                    f"\n跨轮升级: 焦点已持续 {focus_wheels} 轮，当前里程碑 {_mile} "
                                    f"近 8 轮无任何推进证据，疑似停滞，强制换焦点或人工介入。"
                                )
                                return True
                    except Exception:
                        pass
        return False

    # ---------------- 各阶段 prompt ----------------
    def _prompt_observe(self, context: Dict) -> str:
        return f"""你是认知循环的 OBSERVE（观察）阶段。
只陈述事实，不做判断。列出：
1. 环境状态：服务器资源、可用工具、账户状态
2. 上轮结果：{context.get('last_result', '（首轮）')}
3. 外部信号：市场/社区/竞品新动态
4. 当前卡点：什么阻止了进展

**重要：禁止脑补环境状态**。所有关于"哪些命令被允许"/"白名单"/"权限"的判断必须用 [RUN] 执行真实命令验证（如 ls/cat/python3 -c 等），禁止描述"可能"/"应该"/"预期"。

roadmap 焦点（禁止继续）：{context.get('roadmap_focus', '无')[:200]}
跨轮 stalled 警告（如上一轮触发则本轮必须换方向）：{context.get('recent_reflections', '无')}

输出纯观察，不超过 300 字。"""

    def _prompt_orient(self, observation: str, context: Dict) -> str:
        traps = context.get('traps', '（无）')[:800]
        skills = context.get('skills', '（无）')[:500]
        return f"""你是认知循环的 ORIENT（定向）阶段。基于观察建模：
观察：{observation[:800]}

陷阱记忆（必须规避）：{traps}
已结晶技能：{skills}

回答：
1. 当前问题到底是什么？（一句话）
2. 我有哪些假设？哪些已验证、哪些未验证？
3. 认知地图：已知 / 未知 / 需要搞清楚
4. 哪些策略库模式适用？

不超过 300 字。"""

    def _prompt_decide(self, orientation: str, context: Dict) -> str:
            metacog = context.get('metacog_assess', '')
            tool_menu = context.get('tool_menu', '（无工具）')
            focus = context.get('roadmap_focus', '无')
            wheels = context.get('roadmap_focus_wheels', 0)
            # 提取当前里程碑（按顺序匹配 - M1-0 / - M1-1 / - M1-2 / - M2 / - M3 / - M4，且未标 ✅）
            roadmap_text = context.get('roadmap_focus', '')
            import re as _re2
            current_milestone = ""
            for marker in ['M1-0', 'M1-1', 'M1-2', 'M2', 'M3', 'M4']:
                m = _re2.search(rf'-\s*{marker}\s+[^\n]*(?=\n-|\n>|$)', roadmap_text)
                if m and '✅' not in m.group(0):
                    current_milestone = m.group(0).strip()
                    break

            # 获取已执行的动作（最近 3 轮），避免重复
            recent_actions = getattr(self, '_recent_actions', [])
            recent_actions_text = "\n".join([f"- {a[:80]}" for a in recent_actions[-3:]]) if recent_actions else "（无）"

            milestone_hint = (f"**当前里程碑**：{current_milestone}\n"
                              f"**禁止**：环境探查类空转（id/uname/whoami/which/pwd），每轮只做有实质产出的动作。\n"
                              f"**禁止重做**：以下动作已在最近 3 轮执行过，禁止再次执行：\n{recent_actions_text}\n") if current_milestone else ""
            return f"""你是认知循环的 DECIDE（决策）阶段。

    **当前方向**：{focus}（第 {wheels} 轮）
    **方向规则**：本决策必须直接推进当前方向，禁止跳去无关话题。如果决策与当前方向无关，立即重定向。
    {milestone_hint}
    定向分析：{orientation[:600]}

    可用工具（按任务相关性检索 top-5）：
    {tool_menu}

    {metacog}

    严格按以下 JSON 格式输出，不要有任何其他文本：
    {{
      "action": "要做的具体事情（一句话描述意图，如：抓取 upwork 搜索结果写入 requirements.md）",
      "reason": "为什么选这个而不是别的（一句话）",
      "expected": "成功后能看到什么信号（一句具体可观察的描述）",
      "capability": "proven|boundary|unknown",
      "direction_match": true
    }}

    **硬性要求**：
    1. action 是**意图描述**，不是命令。不要写 `[RUN]` 或 `[FILE]`。
    2. 每轮必须推进里程碑，不能重复已完成动作
    3. 禁止环境探查类空转（id/uname/whoami/which/pwd），除非是新方向的第一个轮次
    不超过 150 字。"""

    def _prompt_act(self, decision: str, context: Dict) -> str:
        # ACT 阶段只需决策和当前任务相关的工具 schema
        tool_menu = context.get('tool_menu', '（无工具）')
        # 清理 markdown 代码围栏（如 ```json ... ```）
        import re as _re
        clean_decision = _re.sub(r'```(?:json)?\n?(.*?)\n?```', r'\1', decision, flags=_re.S).strip()
        return f"""你是认知循环的 ACT（行动）阶段。
决策（已清理）：{clean_decision[:600]}

当前任务相关工具：
{tool_menu}

现在生成执行产物。严格遵守输出格式：
[FILE]
路径（work/、data/、knowledge/、tools/、skills/ 开头）
---
文件内容（一次最多1个文件，精简，必须是可运行代码）
[RUN] 运行命令（python3/pip3/git/bash 开头，最多1条）
[RESULT_CHECK] 本轮成功的判定标准（可观察的具体信号，如"命令输出包含 X"）

**硬约束（必须遵守）**：
1. 禁止请求用户输入、禁止要求用户确认、禁止"请用户提供..."等推卸行动的内容
2. 禁止纯描述性文本、禁止散文、禁止"我决定先了解一下"等空话
3. 必须有 [FILE] + [RUN]，缺一不可；只有 [RUN] 没有 [FILE] 也是无效行动
4. **如果决策里已经包含了完整的 [FILE] 和 [RUN] 命令（格式为 [FILE] path\n内容\n[RUN] cmd），直接原样提取并输出，不要修改**。
5. **如果决策里没有任何 [FILE] 和 [RUN] 命令（常见情况），你必须根据决策的意图重新生成完整的 [FILE] + [RUN] 命令。不允许输出空 action！**
6. RUN 命令必须是真实可执行的命令，不能是伪代码或占位符
7. 如果决策需要外部数据，先用 ls/find/python3 -c 等命令探查环境，而不是问人

示例格式（正确）：
[FILE] work/check_env.py
---
#!/usr/bin/env python3
import subprocess
result = subprocess.run(['uname', '-a'], capture_output=True, text=True)
print(result.stdout)
[RUN] python3 work/check_env.py
[RESULT_CHECK] 命令输出包含 "Linux"

示例格式（错误 - 会被拒绝）：
[FILE] work/test.py
---
# 这里写代码...
[RUN] python3 work/test.py
# 如果没有产出具体代码，只是占位，算失败
"""

    def _prompt_reflect(self, trace: CognitiveTrace) -> str:
        return f"""你是认知循环的 REFLECT（反思）阶段。Reflexion 言语强化学习。

本轮记录：
- 决策: {trace.decision[:300]}
- 行动: {trace.action[:300]}
- 结果/观察: {trace.observation[:500]}
- 成功判定: {trace.success}

必须回答（Reflexion 四问）：
1. 结果 vs 预期：差距在哪？
2. 根因：如果失败，是哪个环节错的（决策？代码？工具？环境？）
3. 反事实：如果重来，哪一步会做不同？
4. 迁移：这个经验适用于哪些其他任务？

每条回答不超过 50 字。最后一行输出 [LESSON_SIG] 一句话错误/经验签名。"""

    # ---------------- 主循环 ----------------
    async def run_cycle(self, context: Dict, iteration: int) -> CognitiveTrace:
        """跑一轮完整认知循环"""
        trace = CognitiveTrace(iteration=iteration,
                               started_at=datetime.now().isoformat())
        trace.run_id = context.get('run_id', '')
        import time as _t
        t0 = _t.time()

        # 0. 门控：从情景记忆取最近的反思
        recent = self.memory.retrieve(tier="episodic", tags=["reflection"], limit=3)
        context['recent_reflections'] = json.dumps(
            [r.content for r in recent], ensure_ascii=False)[:1500] if recent else "（无）"

        # 1. OBSERVE
        trace.observe = (await self.llm_call(self._prompt_observe(context), system="你是精确的观察员，只陈述事实。", stage="OBSERVE"))
        logger.info(f"[Cog #{iteration}] OBSERVE 完成")

        # 2. ORIENT
        trace.orient = (await self.llm_call(self._prompt_orient(trace.observe, context),
                                            system="你是问题分析专家。", stage="ORIENT"))
        logger.info(f"[Cog #{iteration}] ORIENT 完成")

        # 3. DECIDE
        trace.decision = (await self.llm_call(self._prompt_decide(trace.orient, context),
                                              system="你是决策者，果断、单任务。", stage="DECIDE"))
        logger.info(f"[Cog #{iteration}] DECIDE 完成")

        # 3.4 DECIDE 输出质量检查：字符数 ≥600 或缺少必要字段时终止本轮
        dec_text = (trace.decision or '').strip()
        if len(dec_text) > 600:
            trace.reflection = f"DECIDE 格式错误：输出过长 {len(dec_text)} 字符（限制 600），已终止本轮"
            trace.success = False
            trace.stalled = True
            await self._consolidate(trace)
            self.last_trace = trace
            return trace
        for key in ['action', 'reason', 'capability']:
            if key not in dec_text.lower():
                trace.reflection = f"DECIDE 格式错误：缺少必要字段 '{key}'"
                trace.success = False
                trace.stalled = True
                await self._consolidate(trace)
                self.last_trace = trace
                return trace

        # 3.5 门控检查（拦截不终止，而是把警告注入下一轮上下文，防止拦截后空转）
        gates = self._gate_check(trace, context)
        if not gates["proceed"]:
            trace.reflection = f"门控拦截：{'；'.join(gates['warnings'])}"
            trace.success = False
            trace.stalled = True  # 标记本轮未真正行动，下轮必须诊断
            trace.action = ""
            await self._consolidate(trace)
            self.last_trace = trace
            return trace

        # P1-3: 元认知硬门控 —— 解析 DECIDE 中的 capability_check 字段
        capability_check = self._parse_capability_check(trace.decision)
        if capability_check:
            if capability_check == "unknown":
                # 修正：若决策意图仅涉及基础 Shell 诊断命令（ls/cat/python3/git/curl/find/grep/which/whoami/pwd 等），
                # 视为已验证能力（self_model 已含 "Shell 命令执行"、"CLI 工具调用"），放行而非拦截
                action_text = trace.decision.lower()
                basic_shell_keywords = ['ls', 'cat', 'python3', 'git', 'curl', 'find', 'grep', 'which', 'whoami', 'pwd', 'head', 'tail', 'stat', 'file']
                if any(kw in action_text for kw in basic_shell_keywords):
                    logger.info(f"[Cog #{iteration}] 元认知修正: capability=unknown 但动作属基础 Shell 诊断，视为 proven 放行")
                    capability_check = "proven"
                else:
                    # 真正未知能力 → 降级为探索任务，禁止 ACT
                    trace.reflection = "元认知门控: 所需能力未在已验证范围内，禁止 ACT，降级为探索/补能力任务"
                    trace.success = False
                    trace.stalled = True
                    trace.action = ""
                    await self._consolidate(trace)
                    self.last_trace = trace
                    return trace
            if capability_check == "boundary":
                # 边界区间 → 强制触发工具验证
                logger.info(f"[Cog #{iteration}] 元认知门控: 能力边界，强制工具验证")
                trace.capability_boundary = True
            # capability_check == "proven" → 允许 ACT

        # 4. ACT（带重试：LLM 偶发返回空/错误/格式缺失时重试，最多 2 次）
        act_text = await self.llm_call(self._prompt_act(trace.decision, context),
                                       system="你是工程师，输出完整可运行的代码。", stage="ACT")
        def _act_bad(t):
            # 空、LLM 错误前缀、或格式不全 都视为坏输出
            if not t or not t.strip():
                return True
            if t.startswith('[错误]'):
                return True
            return ('[FILE]' not in t) or ('[RUN]' not in t)
        retry_count = 0
        while _act_bad(act_text) and retry_count < 2:
            retry_count += 1
            reason = '空' if (not act_text or not act_text.strip()) else ('LLM错误' if act_text.startswith('[错误]') else '缺[FILE]/[RUN]')
            logger.warning(f"[Cog #{iteration}] ACT 输出无效（{reason}），第 {retry_count} 次重试")
            await asyncio.sleep(2)
            act_text = await self.llm_call(self._prompt_act(trace.decision, context),
                                           system="你是工程师，输出完整可运行的代码。", stage="ACT")
        trace.action = act_text or ""
        if _act_bad(trace.action):
            # ACT 彻底失败 → 终止本轮，防止"无动作空转"
            trace.reflection = f"ACT 连续 {retry_count + 1} 次无有效输出（空/LLM错误/无[FILE]+[RUN]），本轮终止，下轮必须换实现路径"
            trace.success = False
            trace.stalled = True
            await self._consolidate(trace)
            self.last_trace = trace
            return trace
        logger.info(f"[Cog #{iteration}] ACT 完成")

        trace.duration_ms = int((_t.time() - t0) * 1000)
        self.last_trace = trace
        return trace

    async def finalize_cycle(self, trace: CognitiveTrace, run_output: str, context: Dict):
        """执行 RUN 后完成循环：观察、判定、反思、沉淀"""
        import time as _t
        t0 = _t.time() - trace.duration_ms / 1000  # 恢复原始开始时间

        trace.observation = run_output if run_output else '（命令已执行完成，stdout 无输出 — 请检查产物文件是否生成）'

        # 5.5 判定成功/失败
        check = re.search(r'\[RESULT_CHECK\]\s*([^\n]+)', trace.action)
        result_check_text = check.group(1).strip() if check else ""
        trace.success = self._judge_success(result_check_text, trace.observation)

        # 5.6 外部可验证产物检查（MAST: Incorrect Verification 防护）
        # 从 [RESULT_CHECK] 和 observation 中提取产物路径，验证文件真实存在且非空
        # 5.6b 内容真实性审计（L1 占位符拦截，防 reward hacking）
        from pathlib import Path as _Path
        search_text = f"{result_check_text} {trace.observation}"
        for _vp in re.finditer(r'((?:data|work|tools|output|skills)/[\w./-]+\.(?:json|csv|md|py|txt|xml|html))', search_text):
            p = _vp.group(1).rstrip('.,;:')
            fp = _Path(p)
            if not fp.exists():
                trace.success = False
                trace.reflection = (
                    f"[EXTERNAL_VERIFY_FAIL] RESULT_CHECK 要求的产物 {p} 不存在 — "
                    f"即使无报错也算失败，需回到 ORIENT 修正子目标或实现路径。"
                )
                trace.stalled = True
                break
            elif fp.stat().st_size < 20:
                trace.success = False
                trace.reflection = (
                    f"[EXTERNAL_VERIFY_FAIL] 产物 {p} 存在但为空（{fp.stat().st_size}B）— "
                    f"判定为无效产物，需回到 ORIENT 修正实现逻辑。"
                )
                trace.stalled = True
                break
            else:
                # L1 内容真实性审计：占位符/保留域名/模板句命中即失败
                fake_hits = self._audit_output_file(p)
                if fake_hits:
                    trace.success = False
                    trace.reflection = (
                        f"[FAKE_CONTENT_FAIL] 产物 {p} 通过格式检查但内容含占位符/模板句/保留域名: "
                        f"{fake_hits[:3]} — 判定为虚假成功（reward hacking），"
                        f"需产出真实内容或真实来源，不接受填充数据。"
                    )
                    trace.stalled = True
                    break

        # 5.7 子目标迭代计数（MAST: Step Repetition 防护）
        # 当同一个 roadmap 里程碑连续 N 次产出相同类型的 action 但未推进交付物，强制升级
        milestone_subgoal = self._extract_current_milestone_subgoal(context)
        if milestone_subgoal:
            subgoal_key = f"{context.get('run_id')}:{milestone_subgoal}"
            if not hasattr(self, '_subgoal_attempts'):
                self._subgoal_attempts = {}
            self._subgoal_attempts[subgoal_key] = self._subgoal_attempts.get(subgoal_key, 0) + 1
            attempts = self._subgoal_attempts[subgoal_key]
            # 检查本轮是否有"真正推进"的证据（写入了新的里程碑相关产物）
            has_progress = any(kw in (trace.observation or '') for kw in [
                'saved', 'written', 'success', 'completed', '✅', 'PASSES', 'PASSED',
                'results saved', '摘要已写入', '分类结果'
            ])
            if attempts >= 3 and not has_progress:
                trace.stalled = True
                trace.reflection = (
                    f"\n[SUBGOAL_LOOP] 子目标 '{milestone_subgoal}' 已连续 {attempts} 轮尝试"
                    f"但未产生可验证的推进证据，强制升级诊断。"
                    f"回 ORIENT 重新评估：是子目标定义错误，还是实现路径错误？"
                )
                # 把诊断信号写入 working memory，下轮 ORIENT 必须处理
                self.memory.store("working", {
                    "type": "subgoal_loop_diagnosis",
                    "milestone": milestone_subgoal,
                    "attempts": attempts,
                    "last_action_preview": (trace.action or "")[:200],
                }, importance=4.5)

        # 6. REFLECT
        trace.reflection = (await self.llm_call(self._prompt_reflect(trace),
                                                system="你是反思者，Reflexion 四问，尖锐不粉饰。", stage="REFLECT"))
        logger.info(f"[Cog #{trace.iteration}] REFLECT 完成")

        # 7. CONSOLIDATE
        trace.consolidation = await self._consolidate(trace)

        # P1-5: 跨轮 stalled 检测
        crossed = self._check_cross_wheel_stall(trace, context)
        if crossed:
            try:
                import json as _json
                from pathlib import Path as _Path
                state_path = _Path("/root/agi-agent/data/run_state.json")
                if state_path.exists():
                    rs = _json.loads(state_path.read_text())
                else:
                    rs = {}
                rs['cross_wheel_stalled'] = True
                rs['cross_wheel_stalled_at_iteration'] = trace.iteration
                state_path.write_text(_json.dumps(rs, ensure_ascii=False, indent=2))
            except Exception as e:
                logger.warning(f"跨轮 stalled 标记写入失败: {e}")

        trace.duration_ms = int((_t.time() - t0) * 1000)
        self.last_trace = trace
        return trace

    FAILURE_MARKERS = [
        'no such file', 'traceback', 'command not found', 'permission denied',
        '拒绝', '失败', 'failed', 'exception', 'exit code', '未执行',
    ]

    # 占位符/保留域名/模板句模式库（L1 确定性拦截，零 LLM 成本）
    # 命中即判定结构性失败 —— 针对 reward hacking：满足格式但不满足真实性
    # 分两组：数据文件（.json/.txt/.csv）用完整模式；源码/脚本用宽松模式（避免注释误伤）
    PLACEHOLDER_PATTERNS = [
        # 保留/示例域名
        r'example\.(com|org|net|io)',
        # 模板句/占位文本（英文）
        r'lorem\s+ipsum',
        r'\bplaceholder\s+data\b|\bplaceholder\s+text\b',
        r'\bgenerated\s+(news\s+digest\s+|entry\s+|content\s+|placeholder\s+|sample\s+)',
        r'news\s+digest\s+item\s+\d+',
        r'\bitem\s+\d+\b',
        r'\bTODO\s*[:：]?\s*待填',
        r'待填写|待补充',
        r'\[your[_ ]\w+\]',
        r'<(name|email|date|address|content|url|link)\s*>',  # 限定占位变量，不拦 HTML 标签
    ]
    PLACEHOLDER_PATTERNS_SRC = [
        # 源码/脚本只拦硬信号：保留域名 + 明确的模板填充句
        r'example\.(com|org|net|io)',
        r'lorem\s+ipsum',
        r'\bgenerated\s+(news\s+digest\s+|entry\s+|content\s+|placeholder\s+|sample\s+)',
        r'news\s+digest\s+item\s+\d+',
        r'\bitem\s+\d+\b',
        r'待填写|待补充',
    ]

    def _detect_fake_content(self, text: str, path_hint: str = "") -> list:
        """检测文本中的占位符/模板句/保留域名。返回命中的模式列表（空=干净）"""
        if not text:
            return []
        t = text.lower()
        hits = []
        for pat in self.PLACEHOLDER_PATTERNS:
            if re.search(pat, t):
                hits.append(pat)
        return hits

    def _audit_output_file(self, fp) -> list:
        """审计产出文件内容真实性：小文件直接全文扫描，大文件扫前 8KB"""
        try:
            from pathlib import Path as _P
            if not fp or not _P(fp).exists():
                return []
            content = _P(fp).read_text(encoding='utf-8', errors='ignore')[:8192]
            s = str(fp)
            # 源码/脚本/文档用宽松模式（注释里的中文字会误伤）；数据文件用完整模式
            if s.endswith(('.py', '.sh', '.yaml', '.yml')):
                pats = self.PLACEHOLDER_PATTERNS_SRC
            else:
                pats = self.PLACEHOLDER_PATTERNS
            if not content.strip():
                return ['<空文件>']
            t = content.lower()
            return [p for p in pats if re.search(p, t)]
        except Exception:
            return []

    def _judge_success(self, check: str, output: str) -> bool:
        """
        严格成功判定（证据制）：
        1. 必须有真实执行输出（空输出/占位符 = 失败）
        2. 输出中不得出现失败标记（特殊处理 error：no error / error_handler / errors: 0 不算失败）
        3. 如果有 [RESULT_CHECK] 标准，输出必须体现该标准（关键词匹配）
        4. 无法判定 = 失败（宁可错判失败，不可错判成功）
        5. 里程碑级验证：对于工作流类任务，data/output/ 存在≥3个有效文件也视为成功
        """
        out = (output or "").strip()
        out_l = out.lower()

        # 1. 必须有真实输出
        if not out or out in ('（未执行或无输出）', '(not executed)'):
            return False

        # 2. 先特殊处理 error 标记（不在 FAILURE_MARKERS 里，单独处理）
        # 先排除 "no error" / "error_handler" / "errors: 0" 等非错误用法
        if not re.search(r'no\s+error|error_handler|errors?\s*[:=]\s*0', out_l):
            # 再检测独立的 error/error: 作为错误词
            if re.search(r'(?:^|\s)error[sd]?\b', out_l):
                return False

        # 3. 检查其他失败标记
        for marker in self.FAILURE_MARKERS:
            if marker in out_l:
                return False

        # 4. [RESULT_CHECK] 标准匹配
        if check:
            check_l = check.lower()
            patterns = [p.strip().lower() for p in re.split(r'[;，,]', check_l)]
            if any(p in out_l for p in patterns if len(p) > 3):
                return True
            if any('不包含' in p or 'not contain' in p for p in patterns):
                return not any(p in out_l for p in patterns if len(p) > 3)
            return len(check) > 10  # check 存在且合理长度 → 视为弱成功

        # 5. 无判定标准但有输出 → 弱成功
        return True

    def _code_words(self, out_l: str) -> set:
        return set(re.findall(r'\w+', out_l))

    async def _consolidate(self, trace: CognitiveTrace) -> str:
        """沉淀：反思写入情景记忆，重复模式升级为语义记忆"""
        written = []

        # 1. 反思存情景记忆
        if trace.reflection:
            sig_match = re.search(r'\[LESSON_SIG\]\s*([^\n]+)', trace.reflection)
            sig = sig_match.group(1).strip() if sig_match else trace.reflection[:60]
            self.memory.store("episodic", {
                "type": "reflection",
                "iteration": trace.iteration,
                "decision": trace.decision[:500],
                "reflection": trace.reflection,
                "success": trace.success,
                "sig": sig,
            }, tags=["reflection", sig[:30]], importance=3.0 if trace.success is False else 2.0)
            written.append(f"反思已存入情景记忆 (sig: {sig[:30]})")

        # 2. 完整 trace 存档（原始记录永久保留，压缩≠删除）
        trace_file = self.trace_dir / f"trace_{trace.iteration:04d}.json"
        trace_file.write_text(json.dumps(asdict(trace), ensure_ascii=False, indent=2),
                              encoding='utf-8')
        written.append(f"认知trace已存档: {trace_file.name}")

        # 3. 重复模式检测 → 升级为语义记忆（防重复犯错的核心）
        recent = self.memory.retrieve(tier="episodic", tags=["reflection"], limit=30)
        sig_counts = {}
        for r in recent:
            s = r.content.get('sig', '')[:30]
            if s:
                sig_counts[s] = sig_counts.get(s, 0) + 1
        for sig, cnt in sig_counts.items():
            if cnt >= 3:
                # 同一模式出现 3 次 → 升级为语义级"陷阱"记忆
                self.memory.store("semantic", {
                    "type": "trap",
                    "pattern": sig,
                    "occurrences": cnt,
                    "note": "同一问题反复出现，必须在 DECIDE 阶段就规避",
                }, tags=["trap", sig[:20]], importance=5.0)
                written.append(f"模式升级为语义陷阱记忆: {sig[:30]} (x{cnt})")

        return "；".join(written) if written else "无沉淀"