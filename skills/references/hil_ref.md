# Human-in-the-Loop - Critical Decision Interruption

## When Interruption Triggers (`_needs_human_approval`)
The agent will auto-pause and ask for confirmation when the decision contains any of:
- **换方向 / 新方向 / pivot** — changing the main direction
- **推送.*github / push.*github / 发布.*release / release** — publishing to public repo
- **申请.*账号 / 注册.*平台** — applying for new accounts/services
- **删除.*代码 / 删除.*文件 / rm /** — deleting code/files

## Interruption Workflow
1. Agent calls `memory.interrupt(reason)` → writes interrupt marker to checkpoint
2. Agent sends Feishu message to owner:
   ```
   🚨 关键决策确认 (int_id)
   决策: {决策摘要}
   请回复: /approve int_id 确认执行，或 /reject int_id 取消
   ```
3. Agent polls every 10s until interrupt marker is cleared or rejected
4. **If user replies `/approve int_id`**: interrupt cleared, execution resumes
5. **If user replies `/reject int_id`**: action cleared, success=False, reflection records "user rejected"

## Owner Response Format
- `/approve int_id` — execute the paused decision
- `/reject int_id` — cancel the paused decision

## Examples
**Trigger: "换方向" in decision**
```
🚨 关键决策确认 (int_20261029_1500)
决策: 明天改做 AI 内容生成 instead of GitHub Action
请回复: /approve int_20261029_1500 确认执行，或 /reject int_20261029_1500 取消
```

**Trigger: "推送 github" in decision**
```
🚨 关键决策确认 (int_20261029_1501)
决策: 将 work/ 目录推送到 GitHub仓库
请回复: /approve int_20261029_1501 确认执行，或 /reject int_20261029_1501 取消
```