# Benchmark Runner - Quick Reference

## 5 Fixed Tasks (0-1 each, total 0-5)

### 1. github_api
- **Action**: Use github tool to fetch repos with `stars:>10000`, limit=3
- **Pass**: Returns ≥3 repos → 1.0; otherwise fallback score 0.3

### 2. code_gen
- **Action**: Write Python function + 3 asserts via LLM
- **Pass**: `returncode=0` + all asserts pass → 1.0; function exists but fails → 0.3; no function → 0.0

### 3. web_fetch
- **Action**: Fetch https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd
- **Pass**: extracted price is within 1 order of magnitude of actual → 1.0; reasonable approx → 0.5; fail → 0.0

### 4. pr_analysis
- **Action**: Analyze sample PR diff, find ≥1 real bug
- **Pass**: identifies bug + correct reason → 1.0; identifies bug partially → 0.5; no bug found → 0.0

### 5. doc_writing
- **Action**: Write 300-word technical article
- **Pass**: has title (≥h1-h3), bullet points, code block ```, length ≥200 → 1.0; partial → 0.3; too short/no structure → 0.0

## History File (`data/benchmarks.json`)
```json
[
  {
    "date": "2026-10-29T15:12:33",
    "scores": {"github_api": 1.0, "code_gen": 0.0, "web_fetch": 0.5, "pr_analysis": 0.0, "doc_writing": 0.0},
    "total": 1.5,
    "max": 5.0,
    "delta_vs_last": null,
    "best_ever": 1.5
  }
]
```

## Evolution Trigger
- Every 8 iterations during the nightly evolution phase
- Results feed into `MetacognitiveMonitor.update_self_model()` as capability/limitation evidence
- Report sent to Feishu every 8 rounds includes: total score, delta vs last, best ever

## Quick Score Interpretation
- 0-1: 起步阶段，核心能力尚未建立
- 2-3: 进步阶段，某项能力已跑通，仍有明显短板
- 4+: 进阶阶段，大部分能力已验证，朝着目标稳步前进