class_skills:
  - name: "metacognitive_monitor"
    triggered_when: "agent needs to decide what it can/cannot do before taking action"
    description: "内在元认知自我模型 - tracks capabilities, limitations, uncertainty, and learning plan. DECIDE phase must output assessment before executing."
    content: |
      ## Metacognitive Monitor - Self-Assessment Before Decision
      
      1. **Assessment Trigger**: Before every DECIDE stage, run `assess_for_decision(decision_text)`.
      2. **Output Format**: The prompt injects a block:
         ```
         【自我模型对照（决策前必做）】
         已验证能力: 已验证能力列表
         已知局限: 已知局限列表
         学习中: 学习中计划列表
         要求：本轮决策必须在开头一句话回答——「所需能力是否在已验证能力内？若不在，是补能力（写脚本/查文档）还是换任务？」缺能力时禁止假装能做，必须先安排补能力的具体步骤。
         ```
      3. **Self-Model Update**: Every 8 iterations (after benchmark), run `update_self_model(reflections, bench_report)`. This writes to `data/self_model.json`:
         - `capabilities`: list of {name, evidence, confidence}
         - `limitations`: list of {name, evidence, mitigation}
         - `uncertainty`: top 3 unresolved questions
         - `learning_plan`: next planned capability build
      4. **Important**: If capabilities are insufficient for the DECIDE action, the agent must explicitly choose between (a)补能力 (write code/documentation), (b)换任务, or (c) proceed with reduced scope and document the gap.
      5. **LLM Prompt**: The assessment output is injected as a system message block into the DECIDE LLM call.
    
    references: []
    scripts: []
    templates: []
  - name: "constitution_engine"
    triggered_when: "agent needs structured rules distilled from experience to guide future decisions"
    description: "蒸馏经验为宪法 - 将反思编译为分类规则，每 8 轮增量合并。包含风险规避、开发规范、策略偏好等分类。"
    content: |
      ## Constitution Engine - Experience Distillation as Rules
      
      1. **Distillation Trigger**: Every 8 iterations (during evolution phase).
      2. **Input**: Recent reflections (episodic memory with sig tags), grouped by similarity.
      3. **Output Format**: Markdown `constitution.md` with sections:
         ```
         # 探索者-α 宪法
         ## 开发规范
         - 代码写完必须立即运行验证，不假装成功
         - MVP 必须端到端闭环
         
         ## 风险规避
         - 禁止在公开仓库写凭证
         - 任何涉及真实资金流动的操作，执行前必须 [ASK] 主人确认。
         
         ## 策略
         - 每轮决策前必须完成自评
         
         ## 工具与环境
         - 只允许安全命令（python/git/pip/curl 等）
         - 危险命令自动拒绝
         
         ## 沟通汇报
         - 每 8 轮向主人发送进度汇报
         - 宪法已蒸馏于: {date}
         ```
      4. **Incremental Merge**: New rules are merged with existing - keep both if they address different concerns, delete only exact duplicates.
      5. **LLM Prompt**: The distilled constitution is injected as context block into every subsequent OBSERVE/ORIENT/DECIDE cycle.
    
    references: []
    scripts: []
    templates: []
  - name: "benchmark_runner"
    triggered_when: "agent needs quantitative self-evaluation across fixed tasks to measure progress"
    description: "固定 5 任务基准，每 8 轮跑一次，总分 0-5。包含 GitHub API / 代码生成 / 网页抓取 / PR 分析 / 文档写作。成绩写入 benchmarks.json 并用于 self_model 更新。"
    content: |
      ## Benchmark Runner - Fixed-Progress Evaluation
      
      1. **Trigger**: Every 8 iterations during the evolution phase.
      2. **5 Fixed Tasks** (scored 0-1 each, total 0-5):
         - `github_api`: Use github tool to fetch repos with stars>10000
         - `code_gen`: Write runnable Python function + 3 asserts
         - `web_fetch`: Extract specific data from public API page
         - `pr_analysis`: Analyze sample PR diff for bugs
         - `doc_writing`: Write 300-word technical article with title, bullet points, code block
      3. **Scoring**: Each task returns a float 0.0-1.0. Total = sum of 5 scores.
      4. **History**: Scores are appended to `data/benchmarks.json` with:
         - `date`, `total`, `scores`, `delta_vs_last`, `best_ever`
      5. **Integration**: Benchmark results feed into `MetacognitiveMonitor.update_self_model()` as evidence for capability/limitation tracking.
      6. **Prompt Injection**: The scores and delta are included in the 8-iteration evolution report sent to Feishu.
    
    references: []
    scripts: []
    templates: []