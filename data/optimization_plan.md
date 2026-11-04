# 探索者-α 升级优化计划

## 执行状态总览

| 层级 | 任务 | 状态 | Commit |
|------|------|------|--------|
| **P0-1** | 凭证结构隔离：移至 secrets/、gitignore、命令黑名单 | ✅ 完成 | 37ed321 |
| **P0-2** | 工具 Schema 契约化：when_not_to_use、分类菜单、秘密写入拦截 | ✅ 完成 | c453813 |
| **P1-1** | 元认知硬门控：DECIDE 必须输出 capability_check、门控解析/拦截 | ✅ 完成 | 5636db7 |
| **P1-2** | 轮内失败升级：连续 2 次失败 → stalled 标记 → 下轮强制诊断 | ✅ 完成 | 5636db7 |
| **P1-3** | 模型分层路由：按 stage 路由（FREELLMAPI 目前全 auto）+ 语义缓存 | ✅ 完成 | 5636db7 |
| **P2-1** | 策略并行分叉：ORIENT→DECIDE 间加演绎+反事实两路径+仲裁 | ⏳ 待定 | — |
| **P2-2** | loop score / calibration 监控：重复动作/置信度偏差自动告警 | ⏳ 待定 | — |
| **不做** | 事件驱动改造、PostgreSQL、Wasm 沙箱、语义缓存（已在模型路由里） | 📝 记录在案 | — |

---

## 关键改动摘要

### P0 安全结构隔离
- `credentials.yaml` 移出 Agent 可读范围 → `secrets/credentials.yaml` (chmod 600)
- `tools/credential_proxy.py`：白名单工具暴露（github_api、email_latest_code、paypal_status），返回值 mask
- `_run_cmd` 黑名单加入 `secrets/`、`credentials.yaml`
- `_write_file` 拒绝写入 secrets/ 路径或含凭证内容
- `.gitignore` 加入 secrets/，git 历史已移除

### P0 工具 Schema 契约化
- `@tool` 装饰器强制 `when_not_to_use` 参数、分类 category
- `tool_menu_text(max_per_category=5)` 按历史成功率排序、精简 token
- 描述必须含"何时不该用"

### P1 元认知硬门控
- DECIDE 输出**必须**含 `capability_check: proven|boundary|unknown`
- `_parse_capability_check()` 解析并门控：
  - `proven` → 允许 ACT
  - `boundary` → 标记需工具验证，继续但加标记
  - `unknown` → 禁止 ACT，降级为探索任务，清空 action 并反思
- `_gate_check` 新增 stalled 检查：上轮 stalled 本轮不得行动，必须先诊断

### P1 轮内失败升级
- `_record_wheel_failure()` 记录同轮失败计数
- 连续 2 次同类失败 → `trace.stalled=True`，注入反思，下轮 OBSERVE 强制带诊断

### P1 模型分层路由
- `model_routing.py` 定义 6 阶段路由表（当前 FREELLMAPI 全用 auto）
- `_llm_call(stage)` 自动选模型
- OBSERVE 语义缓存（MD5 key + 1h TTL）

---

## 下一步

1. 观察 α 运行 2-3 轮，确认：
   - DECIDE 真的输出 capability_check 字段
   - stalled 机制在连续失败时触发
   - 凭证隔离无回归（工具调用正常、git push 等仍能工作）

2. 若无回归 → 可考虑 P2-1（策略并行）或直接让 α 继续跑产生收入

3. 如 LLM 持续不输出 capability_check → 改为更严格的 JSON schema 强制（Pydantic 输出解析）