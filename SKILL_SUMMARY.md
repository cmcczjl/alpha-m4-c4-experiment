# Skill Library Summary - 探索者-α v2

## Active Class-Level Skills

| Skill Name | Trigger | Core Purpose |
|---|---|---|
| `metacognitive_monitor` | DECIDE phase before every action | 自我模型 + 能力自评 + 更新引擎。确保 agent 知道自己会什么/不会什么，并在不行时明确选择。 |
| `constitution_engine` | Every 8 iterations (evolution phase) | 将反思蒸馏为宪法 Markdown，含开发规范/风险规避/策略/工具与环境/沟通汇报。每次增量合并，防止规则碎片化。 |
| `benchmark_runner` | Every 8 iterations | 固定 5 任务基准（GitHub API / 代码生成 / 网页抓取 / PR 分析 / 文档写作），总分 0-5。成绩写入 benchmarks.json 并用于 self_model 更新。 |

## Support Files (references/)

| File | Topic | Purpose |
|---|---|---|
| `skills/references/metacognitive_ref.md` | 自我评估 | 评估 prompt 块、self-model JSON 结构、快速检查清单 |
| `skills/references/constitution_ref.md` | 宪法治理 | 宪法 Markdown 结构、关键规则速查、合并规则 |
| `skills/references/benchmark_ref.md` | 基准评测 | 5 任务快速参考、评分标准、历史格式、评分区间解读 |
| `skills/references/hil_ref.md` | 人工介入 | 中断触发条件、工作流程、主主回复格式、示例 |

## Support Files (templates/)

| File | Type | Purpose |
|---|---|---|
| `skills/templates/constitution_merge.sh` | Merge script | 将新规则合并入现有宪法的 Bash/Python 脚本 |

## Support Files (scripts/)

| File | Purpose |
|---|---|
| `skills/scripts/run_benchmark.py` | 快速运行 5 任务基准并报告分数的脚本 |

## How to Use

1. **每轮 DECIDE 前**: agent 自动输出 `自我模型对照` 块，要求用户/系统在开头回答能力是否足够
2. **每 8 轮进化**: 三件套同时运行：
   - `constitution_engine` 蒸馏新宪法
   - `benchmark_runner` 跑 5 任务基准
   - `metacognitive_monitor` 更新 self_model.json
3. **关键决策**: 若决策含 `换方向/推送/github/申请账号/删除` 等关键词，agent 自动暂停并发飞书求确认

## Quick Commands

```bash
# Run benchmarks
python3 skills/scripts/run_benchmark.py

# View current self-model
cat data/self_model.json

# View current constitution
cat data/constitution.md

# View benchmark history
cat data/benchmarks.json
```

## Rule References (never edit these standalone)

- 风险红线：资金/合同/KYC/私钥 = 必须 [ASK]
- 方向锁定：roadmap 锁 3 轮内不换
- 验证优先：先验证后花钱
- 技能最低门槛：DECIDE 前必须通过自评