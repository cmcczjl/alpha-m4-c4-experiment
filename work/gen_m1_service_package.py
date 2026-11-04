#!/usr/bin/env python3
"""生成 M1-1 最小可交付 AI Employee 服务包定义"""
import os
import json
from datetime import datetime, timezone

os.makedirs("data", exist_ok=True)

content = """# M1-1 AI Employee 最小可交付服务包

> 生成时间: {ts}
> 数据基线: M1-0 调研（自由职业中位 $27.5/h；自动化专业级 $180-300/h）
> 目标: 定义可立即对外交付的最小服务包，明确分层定价与验收条件

---

## 1. 服务定义

**AI Employee** = 以"雇佣一名员工"的契约形态提供 AI 自动化劳动力，按月/按任务计费，
客户获得的是"一个能持续产出成果的角色"，而非"一次咨询"或"一个工具"。

核心能力域（M1-1 范围）:
- 数据处理与报表自动化（Excel / Sheets / DB → 报表）
- 文档工作流自动化（邮件分类、合同抽取、周报生成）
- 代码辅助与维护（PR review、测试补全、依赖升级）

不在 M1-1 范围:
- 多模态（图像/视频生成）
- 客户面向的对话 agent（M2 再做）
- 自主部署私有模型（M3 再做）

---

## 2. 定价分层（3 档）

| 档位 | 名称 | 月费(USD) | 折算时薪 | 对标 | 交付量 | 适用场景 |
|------|------|-----------|----------|------|--------|----------|
| T1 | AI Intern | $499/mo | ~$20/h | 略低于自由职业中位 $27.5/h | ≤25 任务/月 | 个人/小团队试水，单步任务为主 |
| T2 | AI Associate | $1,800/mo | ~$90/h | 中位与专业级之间 | ≤80 任务/月 + 1 个工作流自动化 | 中小企业固定岗（如数据文员） |
| T3 | AI Specialist | $4,500/mo | ~$225/h | 落在专业自动化区间 $180-300/h | ≤30 任务/月 + 全工作流设计+部署 | 企业级流程自动化项目 |

> 时薪折算按每月 ~25 有效工时计（AI 实际算力时间远大于此，此处为"价值锚点"而非工时计费）。

### 2.1 定价依据
- T1 锚点: M1-0 中位 $27.5/h，AI Intern 定位低于中位（学习期/低复杂度），$20/h 折算合理。
- T3 锚点: M1-0 专业级 $180-300/h，$225/h 落在区间内，对应"交付完整自动化系统"价值。
- T2 锚点: T1 与 T3 之间，$90/h，对应"半自动化+人工衔接"价值带。

---

## 3. 具体交付物规格（M1-1 唯一交付物：自动化报表员工）

### 3.1 交付物名称
**AutoReport Employee v0.1** —— 一个可接入客户数据源、按周自动生成业务报表的 AI 员工。

### 3.2 输入契约
- 数据源（任选其一）:
  - Google Sheets（通过 OAuth 或 CSV 导出）
  - 本地 Excel（.xlsx）
  - PostgreSQL / SQLite（只读连接）
- 配置文件 `employee.yaml`:
  ```yaml
  name: weekly_sales_report
  schedule: "0 9 * * 1"  # 每周一 9 点
  source:
    type: sqlite
    path: ./sample.db
  metrics:
    - revenue_total: SUM(amount)
    - top_customers: GROUP BY customer ORDER BY revenue DESC LIMIT 5
  output:
    format: markdown
    channel: email  # 或 stdout
  ```

### 3.3 输出契约
- 产物: `report_YYYYMMDD.md`（Markdown 格式报表）
- 必含字段:
  - `report_date`: 报表生成日期
  - `period`: 数据覆盖周期
  - `metrics`: 配置中声明的所有指标值
  - `summary`: AI 生成的 ≤200 字自然语言摘要
  - `anomalies`: 若指标环比波动 >20%，列出告警项
- 通道: stdout（M1-1 默认）/ email（M1-2 接入）

### 3.4 技术栈
- Python 3.10+
- pandas（数据处理）
- jinja2（报表模板）
- pyyaml（配置解析）
- sqlite3（内置示例数据源）

---

## 4. 验收条件（可观测字段定义）

每个字段必须在交付时由独立脚本验证，输出 PASS/FAIL。

| 字段 | 类型 | 验收方式 | 通过标准 |
|------|------|----------|----------|
| `package.service_defined` | bool | 检查本文档第 1 节存在 | 非空且含"AI Employee"定义 |
| `package.tier_count` | int | 解析第 2 节表格行数 | ≥ 3 |
| `package.t1_price` | float | 解析 T1 月费 | ≤ $600（低于自由职业中位折算月费） |
| `package.t3_price` | float | 解析 T3 月费 | 在 $180-300/h 折算月费区间内 |
| `package.deliverable_spec` | bool | 检查第 3 节含输入/输出契约 | 均存在 |
| `package.deliverable_input` | bool | 检查含 `employee.yaml` 示例 | 存在且可被 yaml.safe_load 解析 |
| `package.deliverable_output_fields` | list | 解析第 3.3 节必含字段 | 含 report_date / metrics / summary |
| `package.acceptance_fields` | int | 本表行数 | ≥ 6 |
| `deliverable.runnable` | bool | 执行 `python3 -m auto_report --dry-run` | exit code 0 且生成样例报表 |
| `deliverable.report_has_summary` | bool | 检查样例报表含 `summary:` | 非空字符串 |

### 4.1 验收脚本接口（M1-1 须实现）
```bash
python3 -m auto_report --validate
```
输出 JSON:
```json
{{
  "package.service_defined": true,
  "package.tier_count": 3,
  "package.t1_price": 499.0,
  "package.t3_price": 4500.0,
  "package.deliverable_spec": true,
  "package.deliverable_input": true,
  "package.deliverable_output_fields": ["report_date","period","metrics","summary","anomalies"],
  "package.acceptance_fields": 10,
  "deliverable.runnable": true,
  "deliverable.report_has_summary": true
}}
```
全部为 true / 达标即 M1-1 验收通过。

---

## 5. M1-1 边界与后续

- M1-1 只交付 T1 档能力（AutoReport），T2/T3 为定价占位，实现推迟到 M2。
- M1-1 不含计费系统、不含客户面板、不含多租户。
- M1-2 将接入邮件通道 + 第二个交付物（文档工作流）。
""".format(ts=datetime.now(timezone.utc).isoformat())

path = "data/m1_service_package.md"
with open(path, "w", encoding="utf-8") as f:
    f.write(content)

# 写入验证元数据，供下游脚本检查
meta = {
    "file": path,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "tiers": 3,
    "prices": {"T1": 499, "T2": 1800, "T3": 4500},
    "deliverable": "AutoReport Employee v0.1",
    "acceptance_field_count": 10,
}
meta_path = "data/m1_service_package.meta.json"
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=2, ensure_ascii=False)

print(f"[OK] wrote {path} ({len(content)} chars)")
print(f"[OK] wrote {meta_path}")
print(f"[META] {json.dumps(meta, ensure_ascii=False)}")