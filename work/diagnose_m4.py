#!/usr/bin/env python3
"""诊断 package_deliverable.py 中 M4_output 路径逻辑，判断根因。"""
import os, re, sys, traceback

TARGET = "work/package_deliverable.py"

def main():
    # 1) 检查脚本是否存在
    if not os.path.isfile(TARGET):
        print(f"[FAIL] 目标脚本不存在: {TARGET}")
        print("[HINT] 前置步骤可能未生成该脚本，需回溯产出链。")
        # 尝试列出 work/ 目录内容辅助判断
        if os.path.isdir("work"):
            print("[CONTEXT] work/ 目录现有文件:")
            for f in sorted(os.listdir("work")):
                print(f"  - {f}")
        else:
            print("[CONTEXT] work/ 目录不存在。")
        return

    # 2) 读取源码
    with open(TARGET, "r", encoding="utf-8", errors="replace") as fh:
        src = fh.read()
    lines = src.splitlines()
    print(f"[OK] 已读取 {TARGET}，共 {len(lines)} 行")

    # 3) 定位 M4_output 相关逻辑
    m4_hits = []
    for i, line in enumerate(lines):
        if re.search(r"M4_?[Oo]utput|m4_?[Oo]utput|M4_OUTPUT", line):
            m4_hits.append((i + 1, line.rstrip()))
    if m4_hits:
        print(f"[INFO] 找到 {len(m4_hits)} 处 M4_output 引用:")
        for ln, txt in m4_hits:
            print(f"  L{ln}: {txt}")
    else:
        print("[WARN] 未找到 M4_output 字样，可能变量名不同。")

    # 4) 检查 os.makedirs / Path.mkdir / exist_ok 等目录创建调用
    mkdir_hits = []
    for i, line in enumerate(lines):
        if re.search(r"os\.makedirs|os\.mkdir|Path\(.*\)\.mkdir|mkdir_p|ensure_dir|make_dir|create_dir", line):
            mkdir_hits.append((i + 1, line.rstrip()))
    if mkdir_hits:
        print(f"[INFO] 找到 {len(mkdir_hits)} 处目录创建调用:")
        for ln, txt in mkdir_hits:
            print(f"  L{ln}: {txt}")
    else:
        print("[DIAG] 脚本中未发现任何 makedirs/mkdir 调用 → 根因：脚本缺目录创建逻辑")

    # 5) 检查 M4_output 是否被用作写入路径但无 makedirs 保护
    write_m4 = []
    for i, line in enumerate(lines):
        if re.search(r"open\s*\(.{0,80}M4", line) or re.search(r"shutil\.(make_archive|copy|copytree).{0,80}M4", line) or re.search(r"\.write.{0,40}M4", line):
            write_m4.append((i + 1, line.rstrip()))
    if write_m4:
        print(f"[INFO] M4_output 被用于写入/打包的位置:")
        for ln, txt in write_m4:
            print(f"  L{ln}: {txt}")

    # 6) 检查 import os / pathlib
    has_os = bool(re.search(r"^\s*import\s+os\b|^\s*from\s+os\b", src, re.M))
    has_pathlib = bool(re.search(r"^\s*(import|from)\s+pathlib\b", src, re.M))
    print(f"[INFO] import os: {has_os} | import pathlib: {has_pathlib}")

    # 7) 综合判定
    print("\n" + "=" * 60)
    if not m4_hits:
        print("[VERDICT] 未找到 M4_output 逻辑，需回溯前置步骤是否产出该变量/配置。")
    elif not mkdir_hits:
        print("[VERDICT] 脚本缺 os.makedirs → 一行修复：在写入前加 os.makedirs(m4_output_dir, exist_ok=True)")
    else:
        # 有 makedirs 但仍失败 → 可能是顺序问题或路径变量为空
        # 检查 makedirs 是否在 M4_output 写入之前
        first_mkdir_ln = mkdir_hits[0][0]
        first_write_ln = write_m4[0][0] if write_m4 else 999999
        if first_write_ln < first_mkdir_ln:
            print("[VERDICT] makedirs 在写入之后 → 顺序错误，需调整到写入前")
        else:
            print("[VERDICT] makedirs 存在且在写入前 → 需检查路径变量是否为空/错误，回溯前置步骤")
    print("=" * 60)

    # 8) 额外：打印 M4_output 附近 ±3 行上下文便于人工确认
    if m4_hits:
        print("\n[CONTEXT] M4_output 相关上下文（±3行）:")
        seen = set()
        for ln, _ in m4_hits:
            for ctx in range(max(1, ln - 3), min(len(lines) + 1, ln + 4)):
                if ctx not in seen:
                    seen.add(ctx)
                    marker = " >>> " if ctx == ln else "     "
                    print(f"{marker}L{ctx}: {lines[ctx-1].rstrip()}")

if __name__ == "__main__":
    main()