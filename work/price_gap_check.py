#!/usr/bin/env python3
"""抽样检查 requirements.md 中无价格条目的原始文本，grep 价格模式估真实覆盖率。"""
import os, re, json, subprocess, pathlib

# 探查环境，找到 requirements.md
candidates = []
for root in [".", "data", "data/market_research", "work"]:
    for dirpath, _, files in os.walk(root if os.path.isdir(root) else "."):
        for f in files:
            if f == "requirements.md" or f == "requirements.json":
                candidates.append(os.path.join(dirpath, f))

print("=== 找到的候选文件 ===")
for c in candidates:
    print(c)

# 读取原始文本
raw_text = ""
raw_file = None
for c in candidates:
    if c.endswith(".md"):
        with open(c, "r", encoding="utf-8", errors="replace") as fh:
            raw_text = fh.read()
            raw_file = c
            break

if not raw_text:
    # 尝试 json
    for c in candidates:
        if c.endswith(".json"):
            with open(c, "r", encoding="utf-8", errors="replace") as fh:
                data = json.load(fh)
                raw_text = json.dumps(data, ensure_ascii=False, indent=2)
                raw_file = c
                break

if not raw_text:
    print("!! 未找到 requirements.md 或 requirements.json")
    # 最后兜底：全盘搜索
    result = subprocess.run(
        ["find", "/", "-maxdepth", "5", "-name", "requirements.md", "-type", "f"],
        capture_output=True, text=True, timeout=10
    )
    print("find 结果:", result.stdout)
    if result.stdout.strip():
        raw_file = result.stdout.strip().split("\n")[0]
        with open(raw_file, "r", encoding="utf-8", errors="replace") as fh:
            raw_text = fh.read()
    else:
        raise SystemExit("无法定位 requirements.md，终止")

print(f"\n=== 使用文件: {raw_file} (长度 {len(raw_text)} 字符) ===\n")

# 价格正则模式
price_patterns = [
    (r'\$\s*\d+', "美元符号 $数字"),
    (r'USD\s*\d+', "USD 关键字"),
    (r'\b\d+\s*USD\b', "数字 USD 后缀"),
    (r'bounty', "bounty 关键字 (不区分大小写)"),
    (r'reward', "reward 关键字"),
    (r'prize', "prize 关键字"),
    (r'赏金', "中文 赏金"),
    (r'悬赏', "中文 悬赏"),
    (r'奖金', "中文 奖金"),
    (r'\b\d{2,6}\s*(?:to|-|–)\s*\d{2,6}\s*(?:USD|\$)', "范围价格 N to N USD"),
]

# 将原始文本按条目分割（尝试多种分隔符）
lines = raw_text.split("\n")

# 尝试按条目分块：常见分隔包括 "---", "##", 编号等
entries = re.split(r'(?:\n---\n|\n#{2,}\s|\n\d+\.\s)', raw_text)
entries = [e.strip() for e in entries if e.strip()]

print(f"=== 分割得到 {len(entries)} 个条目 ===\n")

# 对每个条目检测是否含价格
price_regex = re.compile('|'.join(p[0] for p in price_patterns), re.IGNORECASE)

has_price = []
no_price = []

for i, entry in enumerate(entries):
    if price_regex.search(entry):
        has_price.append((i, entry[:200]))
    else:
        no_price.append((i, entry[:200]))

print(f"含价格模式条目: {len(has_price)}")
print(f"无价格模式条目: {len(no_price)}\n")

# 对无价格条目做更细粒度的 grep——逐条打印前 5 个样本
print("=== 无价格条目样本 (前10条) ===")
for idx, (i, snippet) in enumerate(no_price[:10]):
    print(f"\n--- 条目 #{i} ---")
    print(snippet)
    print("---")

# 逐模式统计覆盖率
print("\n=== 逐模式命中统计 ===")
mode_stats = {}
for pat, label in price_patterns:
    matches = re.findall(pat, raw_text, re.IGNORECASE)
    mode_stats[label] = len(matches)
    print(f"  {label:30s} → {len(matches)} 次命中")

# 总覆盖率
total = len(entries) if entries else 1
coverage_pct = len(has_price) / total * 100

# 写入结果文件
out_dir = "data/market_research"
pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)
out_path = os.path.join(out_dir, "price_gap_check.txt")

with open(out_path, "w", encoding="utf-8") as out:
    out.write("=" * 60 + "\n")
    out.write("价格缺口检查报告 — requirements.md 无价格条目分析\n")
    out.write("=" * 60 + "\n\n")
    out.write(f"源文件: {raw_file}\n")
    out.write(f"原始文本长度: {len(raw_text)} 字符\n")
    out.write(f"分割条目总数: {len(entries)}\n")
    out.write(f"含价格模式条目: {len(has_price)}\n")
    out.write(f"无价格模式条目: {len(no_price)}\n")
    out.write(f"价格覆盖率: {coverage_pct:.1f}%\n\n")

    out.write("--- 逐模式命中统计 ---\n")
    for label, count in mode_stats.items():
        out.write(f"  {label:30s} → {count} 次\n")

    out.write(f"\n--- 无价格条目样本 (前20条，每条前200字符) ---\n")
    for i, snippet in no_price[:20]:
        out.write(f"\n[条目 #{i}]\n{snippet}\n")

    out.write("\n" + "=" * 60 + "\n")
    out.write("结论:\n")
    if len(no_price) > len(has_price):
        out.write(f"  - 无价格条目 ({len(no_price)}) 多于含价格条目 ({len(has_price)})\n")
        out.write(f"  - 覆盖率仅 {coverage_pct:.1f}%，需确认是数据源缺失还是解析遗漏\n")
        # 检查无价格条目中是否有疑似价格但未被正则捕获的
        suspicious = 0
        for _, snippet in no_price:
            # 检查是否有纯数字 + 货币暗示
            if re.search(r'\b\d{2,5}\b', snippet) and re.search(r'(pay|cost|fee|budget|rate|compensation|salary|stipend|compensat)', snippet, re.IGNORECASE):
                suspicious += 1
        out.write(f"  - 无价格条目中含数字+薪酬关键词的疑似遗漏: {suspicious} 条\n")
    else:
        out.write(f"  - 覆盖率 {coverage_pct:.1f}%，价格信息基本完整\n")

print(f"\n=== 报告已写入 {out_path} ===")