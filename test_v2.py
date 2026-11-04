#!/usr/bin/env python3
"""
v2 架构冒烟测试 - 验证各子系统联通性
1. 三层记忆 读写
2. 工具注册 加载/调用
3. 风险扫描
4. 认知循环（Mock LLM，验证流程）
5. 进化引擎（技能结晶/陷阱审计）
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from memory_tiered import create_memory
import tool_registry
from evolution_engine import risk_check
from cognitive_loop import CognitiveLoop

BASE = Path(__file__).parent
TEST_DB = BASE / "data" / "test_memory.db"
TEST_DB.unlink(missing_ok=True)


class MockLLM:
    """模拟 LLM，返回固定格式"""
    def __init__(self):
        self.calls = 0

    async def __call__(self, prompt, system=None):
        self.calls += 1
        if "OBSERVE" in prompt:
            return "服务器正常，上轮 review.py 运行成功，GitHub token 已配置。"
        if "ORIENT" in prompt:
            return "问题：MVP 还没推到 GitHub。假设：推上去后能被真实 PR 触发。"
        if "DECIDE" in prompt:
            return "决策：创建 GitHub repo 并 push 代码。理由：里程碑需要。"
        if "ACT" in prompt:
            return ("[FILE]\nwork/push_to_github.py\n---\n"
                    "print('push script')\n"
                    "[RUN] python3 work/push_to_github.py\n"
                    "[RESULT_CHECK] 输出包含 OK")
        if "REFLECT" in prompt:
            return ("1. 结果符合预期\n2. 无根因\n3. 无\n4. 迁移到所有部署任务\n"
                    "[LESSON_SIG] git push 成功模式")
        return "ok"


async def main():
    print("=" * 50)
    print("1. 三层记忆测试")
    mem = create_memory(BASE / "data")
    mem.db_path.unlink(missing_ok=True)
    mem._init_db()

    mid1 = mem.store("working", {"event": "test event", "data": [1, 2, 3]},
                     tags=["agent_1"], importance=1.0)
    mid2 = mem.store("episodic", {"type": "reflection", "sig": "git push 成功模式",
                                  "success": True}, tags=["reflection"], importance=2.0)
    mid3 = mem.store("semantic", {"pattern": "knowledge_x"}, tags=["knowledge"], importance=3.0)
    mem.store("procedural", {"name": "git_push_skill", "code": "print(1)",
                             "description": "推代码", "category": "github"},
              tags=["skill", "github"], importance=5.0)

    stats = mem.stats()
    assert stats.get("working") == 1 and stats.get("episodic") == 1, f"stats 错误: {stats}"
    r = mem.retrieve(tier="episodic", tags=["reflection"])
    assert len(r) == 1 and r[0].content["sig"] == "git push 成功模式"
    skills = mem.get_procedural_skills()
    assert len(skills) == 1 and skills[0].content["name"] == "git_push_skill"
    print(f"   ✅ 四层记忆读写正常: {stats}")

    # 语义模式提取
    for i in range(3):
        mem.store("episodic", {"type": "test", "k": i}, tags=["common_pattern"], importance=1.0)
    patterns = mem.extract_semantic_patterns(min_occurrences=3)
    assert len(patterns) >= 1, f"模式提取失败: {patterns}"
    print(f"   ✅ 语义模式提取: {patterns}")

    print("2. 工具注册测试")
    # 从 tools/ 加载 @tool 模块
    # 先注册一个测试工具
    @tool_registry.tool(description="测试工具：加法")
    def add(a: str, b: str) -> int:
        return int(a) + int(b)

    tools = tool_registry.list_tools()
    assert any(t["name"] == "add" for t in tools), "测试工具未注册"
    result = tool_registry.call_tool("add", {"a": "2", "b": "3"})
    assert result["ok"] and result["result"] == 5, f"工具调用失败: {result}"
    menu = tool_registry.tool_menu_text()
    assert "add" in menu
    print(f"   ✅ 工具注册/调用正常，菜单含 {len(tools)} 个工具")

    # 动态工具生成
    dyn = tool_registry.register_dynamic_tool(
        "from tool_registry import tool\n"
        "@tool(description='动态工具：反转字符串')\n"
        "def reverse(s: str) -> str:\n"
        "    return s[::-1]\n")
    assert dyn["ok"] and "reverse" in dyn["registered"], f"动态工具失败: {dyn}"
    r = tool_registry.call_tool("reverse", {"s": "abc"})
    assert r["result"] == "cba"
    print(f"   ✅ 动态工具生成正常: {dyn['registered']}")
    # 动态工具禁止危险模块
    bad = tool_registry.register_dynamic_tool("import subprocess\n@tool()\ndef x():pass")
    assert not bad["ok"]
    print(f"   ✅ 动态工具安全检查正常: 拒绝 subprocess")

    print("3. 风险扫描测试")
    safe = risk_check("写一个 GitHub Action 的 Dockerfile")
    assert not safe["has_risk"]
    risky = risk_check("把 PayPal live 的款项打款给新地址，并转移资金")
    assert risky["has_risk"] and len(risky["flags"]) >= 2
    private_key = risk_check("把助记词写进 public repo 备份")
    assert private_key["has_risk"]
    print(f"   ✅ 风险扫描正常: 安全={not safe['has_risk']}, "
          f"资金={risky['flags'][:3]}, 私钥={private_key['flags'][:2]}")

    print("4. 认知循环测试 (Mock LLM)")
    llm = MockLLM()
    cog = CognitiveLoop(mem, llm, BASE)
    ctx = {"last_result": "上轮输出 OK", "roadmap_focus": "AI 代码审查 MVP",
           "recent_reflections": "（无）"}
    # 注入行动执行结果
    original_judge = cog._judge_success
    trace = None
    # 手动跑各阶段（模拟 run_cycle 但注入 run_output）
    # 直接用 run_cycle，run_output 通过 context 传入
    ctx["run_output"] = "OK\npushed successfully"
    trace = await cog.run_cycle(ctx, iteration=999)
    assert trace.observe and trace.orient and trace.decision and trace.action
    assert trace.reflection and trace.consolidation
    assert trace.success is True
    assert llm.calls >= 5, f"LLM 调用次数不足: {llm.calls}"
    print(f"   ✅ 认知循环完整跑通: {llm.calls} 次 LLM 调用, {trace.duration_ms}ms")
    print(f"      OBSERVE: {trace.observe[:40]}")
    print(f"      DECIDE:  {trace.decision[:40]}")
    print(f"      REFLECT: {trace.reflection[:60]}")
    print(f"      沉淀:    {trace.consolidation}")

    # 验证沉淀落库
    refl = mem.retrieve(tier="episodic", tags=["reflection"], limit=5)
    assert any(r.content.get("iteration") == 999 for r in refl), "反思未落库"
    trace_files = sorted((BASE / "data" / "cognitive_traces").glob("trace_*.json"))
    assert len(trace_files) >= 1, "认知 trace 未存档"
    print(f"   ✅ 反思落库 + trace 存档: {trace_files[-1].name}")

    print("5. 进化引擎测试")
    from evolution_engine import EvolutionEngine
    evo = EvolutionEngine(mem, llm, BASE)
    traps = evo.audit_traps()  # 无失败记录，应返回空
    assert traps == []
    health = await evo.health_check()
    assert "memory_stats" in health
    print(f"   ✅ 陷阱审计: {traps}, 健康检查: {health['memory_stats']}")

    # 失败模式重复 3 次 → 陷阱
    for i in range(3):
        mem.store("episodic", {"type": "reflection", "sig": "GitHub 403 数据中心IP",
                               "success": False}, tags=["reflection"], importance=3.0)
    traps = evo.audit_traps()
    assert len(traps) == 1 and "403" in traps[0], f"陷阱审计失败: {traps}"
    print(f"   ✅ 失败模式→陷阱升级: {traps}")

    # 清理测试数据
    TEST_DB.unlink(missing_ok=True)
    mem.db_path.unlink(missing_ok=True)

    print("=" * 50)
    print("✅ 全部子系统测试通过")


if __name__ == "__main__":
    asyncio.run(main())
