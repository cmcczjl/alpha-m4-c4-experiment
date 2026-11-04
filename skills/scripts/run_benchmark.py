#!/usr/bin/env python3
"""Quick benchmark runner - run all 5 tasks and report scores."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from benchmark_runner import BenchmarkRunner
from memory_tiered import create_memory
import asyncio

async def main():
    mem = create_memory(Path(__file__).parent)
    # Simple mock LLM that returns fixed scores
    async def fixed_llm(p, system=None, max_tokens=None):
        return '{"capabilities":[{"name":"python基础","evidence":"写过脚本","confidence":0.8}],"limitations":[{"name":"GitHub Action 完整闭环","evidence":"两次未完整交付","mitigation":"分阶段先跑通端到端"}],"uncertainty":["如何用 act 本地测试 Action"],"learning_plan":[{"what":"act 本地测试","how":"看文档+试跑","eta":"1轮","status":"plan"}]}'
    
    runner = BenchmarkRunner(mem, fixed_llm, Path(__file__).parent)
    report = await runner.run_all()
    
    # Print summary
    print(f"\n{'='*40}")
    print(f"基准测试结果: {report['total']}/5.0")
    print(f"{'='*40}\n")
    for task, score in report['scores'].items():
        status = "✅" if score >= 0.7 else "⚠️" if score >= 0.3 else "❌"
        print(f"  {status} {task}: {score}")
    print(f"\n相对于上次: {'提升' if report.get('delta_vs_last', 0) > 0 else '无变化' or '首次运行'}")
    print(f" best-ever: {report.get('best_ever', 0)}/5.0")
    print(f"\n详细报告已写入: data/benchmarks.json")

if __name__ == "__main__":
    asyncio.run(main())