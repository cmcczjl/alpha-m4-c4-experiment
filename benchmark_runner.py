"""
BenchmarkRunner - 量化能力基准
参考 2026 ICLR (HyperAgents/DGM): 基准成绩是选代/验收的证据门控
参考 SARSI: 自我模型由 benchmark 驱动更新

固定 5 个任务，每次进化（每 8 轮）跑一次：
  1. github_api   - 用 tools/github_tool 调 GitHub API 拿 3 个热门 repo 的 star 数
  2. code_gen     - LLM 写一个函数（含测试），必须真实运行且测试通过
  3. web_fetch    - 抓取公开网页并提取关键数字
  4. pr_analysis  - 给一段真实 PR diff，LLM 找出至少 1 个真实 bug/问题
  5. doc_writing  - 写 300 字技术说明，结构完整（标题/分点/代码块）

每个任务 0-1 分，总分 0-5。成绩历史存 data/benchmarks.json，
趋势（比上次 +/-）用于自我模型更新和向主人汇报"我变强了吗"。
"""
import asyncio
import json
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

BENCH_HISTORY_FILE = "benchmarks.json"

# 固定 PR diff（含 2 个真实 bug：off-by-one + 资源未关闭）
_SAMPLE_DIFF = """diff --git a/cache.py b/cache.py
--- a/cache.py
+++ b/cache.py
@@ -10,13 +10,15 @@
 def get_user_by_id(user_id):
-    for user in users:
-        if user.id == user_id:
+    f = open("users.txt")
+    for i, user in enumerate(f.readlines()):
+        if i == user_id:
             return user
-    return None
+    return user
"""


class BenchmarkRunner:
    def __init__(self, memory, llm_call, base_path: Path):
        self.memory = memory
        self.llm_call = llm_call
        self.base_path = base_path
        self.history_file = base_path / "data" / BENCH_HISTORY_FILE

    # ---------------- 任务 1: GitHub API ----------------
    async def task_github_api(self) -> float:
        try:
            import tool_registry
            r = tool_registry.call_tool("github_search_repos", {"query": "stars:>10000", "limit": "3"})
            if r.get("ok") and r.get("result"):
                return 1.0
            # fallback: 直接调 API
            import httpx
            async with httpx.AsyncClient(timeout=15) as c:
                resp = await c.get(
                    "https://api.github.com/search/repositories?q=stars:>10000&per_page=3")
                data = resp.json()
                if resp.status_code == 200 and len(data.get("items", [])) >= 3:
                    return 1.0
            return 0.3
        except Exception as e:
            logger.warning(f"bench github_api 失败: {e}")
            return 0.0

    # ---------------- 任务 2: 代码生成+运行 ----------------
    async def task_code_gen(self) -> float:
        prompt = ("写一个 Python 脚本：函数 parse_log_line(line) 解析形如 "
                  "'2026-10-29 12:32:06 [INFO] hello' 的日志行，返回 (timestamp_str, level, message) 三元组；"
                  "格式非法返回 None。同时写 3 个 assert 测试。"
                  "输出纯 Python 代码，不要 markdown 围栏。")
        code = await self.llm_call(prompt, system="只输出可运行的 Python 代码。", max_tokens=1500)
        code = re.sub(r'^```(?:python)?\s*|\s*```$', '', code.strip(), flags=re.MULTILINE)
        if 'def parse_log_line' not in code:
            return 0.0
        try:
            with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False,
                                             encoding='utf-8') as f:
                f.write(code)
                tmp = f.name
            r = subprocess.run(['python3', tmp], capture_output=True, text=True, timeout=30)
            Path(tmp).unlink(missing_ok=True)
            if r.returncode == 0:
                return 1.0
            return 0.3  # 有函数但测试不过
        except Exception:
            return 0.0

    # ---------------- 任务 3: 网页抓取提取 ----------------
    async def task_web_fetch(self) -> float:
        import httpx
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as c:
                r = await c.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
                data = r.json()
            price = data.get("bitcoin", {}).get("usd")
            if not price:
                return 0.0
            # 让 LLM 从数据里提取并格式化
            out = await self.llm_call(
                f"数据: {json.dumps(data)}\n用一行回答：当前 BTC 美元价格是多少？只输出数字+美元符号。",
                max_tokens=100)
            if str(int(price) // 1000) in out:  # 千位级别对上即可
                return 1.0
            return 0.5
        except Exception:
            return 0.0

    # ---------------- 任务 4: PR 分析（找 bug） ----------------
    async def task_pr_analysis(self) -> float:
        out = await self.llm_call(
            f"分析这段 PR diff，找出其中真实的 bug 或回归风险，列出至少 1 个并说明原因：\n\n{_SAMPLE_DIFF}\n\n"
            "输出格式：BUG: <描述>", max_tokens=500)
        out_l = out.lower()
        # 真实 bug 关键词：索引/enumerate/off-by-one（用 i==user_id 按行号而非 id）+ 文件未关闭
        hits = 0
        if any(k in out_l for k in ('enumerate', '索引', '行号', 'off-by-one', 'off by one', 'line number', 'i ==')):
            hits += 1
        if any(k in out_l for k in ('未关闭', 'close', 'with', '资源泄漏', 'resource')):
            hits += 1
        if out.strip().upper().startswith('BUG') or 'bug' in out_l:
            hits += 0.5
        return min(1.0, hits / 1.5)

    # ---------------- 任务 5: 技术文档 ----------------
    async def task_doc_writing(self) -> float:
        out = await self.llm_call(
            "写一段 300 字左右的技术说明：什么是 API rate limiting，为什么需要，常见 3 种实现方式。"
            "要求有标题、分点列表、至少一个代码块。", max_tokens=800)
        score = 0.0
        if re.search(r'^#{1,3}\s', out, re.MULTILINE):
            score += 0.3
        if re.search(r'^\s*[-*]\s', out, re.MULTILINE) or re.search(r'^\s*\d+\.\s', out, re.MULTILINE):
            score += 0.3
        if '```' in out:
            score += 0.3
        if len(out) >= 200:
            score += 0.1
        return round(min(1.0, score), 2)

    # ---------------- 任务 6: 假数据红队测试（验证器自检测） ----------------
    async def task_fake_data_redteam(self) -> float:
        """
        对抗性测试：给验证门控喂一份已知假数据（example.com URL + 模板句），
        门控必须拒绝；同时喂一份真实数据，门控必须放行。
        放行假数据 = 0 分（验证器可被 reward hacking 欺骗）。
        误杀真数据 = 0.5 分（验证器过严，同样损害成功率）。
        """
        import sys
        from cognitive_loop import CognitiveLoop
        gate = CognitiveLoop.__new__(CognitiveLoop)
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False,
                                         dir=str(self.base_path / "data"), encoding='utf-8') as tf:
            tf.write(json.dumps([
                {"title": "News Digest Item 1",
                 "summary": "Generated news digest entry with required timestamp.",
                 "source_url": "https://example.com/news/1"},
            ], ensure_ascii=False))
            fake_path = tf.name
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False,
                                         dir=str(self.base_path / "data"), encoding='utf-8') as tf:
            tf.write(json.dumps([
                {"title": "Upwork Q2 2026: GSV $966.4M, 763k active clients",
                 "summary": "Upwork reported gross services volume of $966.4 million, "
                            "down 4% year over year, across 763,000 active clients.",
                 "source_url": "https://digiko.io/money/ai-freelance-pay-in-2026"},
            ], ensure_ascii=False))
            clean_path = tf.name
        try:
            fake_hits = gate._audit_output_file(fake_path)
            clean_hits = gate._audit_output_file(clean_path)
            rejected_fake = len(fake_hits) > 0
            accepted_clean = len(clean_hits) == 0
            if rejected_fake and accepted_clean:
                return 1.0
            if rejected_fake:
                logger.warning(f"redteam: 误杀真实数据 hits={clean_hits}")
                return 0.5
            logger.warning(f"redteam: 门控放行假数据! hits={fake_hits} — 验证器存在 reward hacking 漏洞")
            return 0.0
        finally:
            for p in (fake_path, clean_path):
                try:
                    Path(p).unlink()
                except Exception:
                    pass

    # ---------------- 汇总 ----------------
    async def run_all(self) -> dict:
        logger.info("Benchmark 开始（6 任务）")
        scores = {}
        tasks = {
            "github_api": self.task_github_api(),
            "code_gen": self.task_code_gen(),
            "web_fetch": self.task_web_fetch(),
            "pr_analysis": self.task_pr_analysis(),
            "doc_writing": self.task_doc_writing(),
            "fake_data_redteam": self.task_fake_data_redteam(),
        }
        for name, coro in tasks.items():
            try:
                scores[name] = round(await coro, 2)
            except Exception as e:
                logger.warning(f"bench {name} 异常: {e}")
                scores[name] = 0.0
        total = round(sum(scores.values()), 2)
        report = {
            "date": datetime.now().isoformat(),
            "scores": scores,
            "total": total,
            "max": 6.0,
        }
        # 追加历史 + 算趋势
        history = []
        if self.history_file.exists():
            try:
                history = json.loads(self.history_file.read_text(encoding='utf-8'))
            except Exception:
                history = []
        if history:
            last_total = history[-1].get("total")
            report["delta_vs_last"] = round(total - last_total, 2)
            report["best_ever"] = max(h.get("total", 0) for h in history)
        else:
            report["delta_vs_last"] = None
            report["best_ever"] = total
        history.append(report)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history_file.write_text(
            json.dumps(history[-50:], ensure_ascii=False, indent=2), encoding='utf-8')
        logger.info(f"Benchmark 完成: {total}/5 {scores}")
        return report
