#!/usr/bin/env python3
import os
import subprocess

# 先尝试直接用 find 查找 pricing.md
result = subprocess.run(
    ['find', '.', '-name', 'pricing.md', '-type', 'f'],
    capture_output=True,
    text=True
)

if result.stdout.strip():
    print("找到文件：")
    for line in result.stdout.strip().split('\n'):
        abs_path = os.path.abspath(line)
        print(abs_path)
else:
    print("未找到 pricing.md，展示目录结构：")
    ls_result = subprocess.run(
        ['ls', '-R', '--color=never'],
        capture_output=True,
        text=True
    )
    print(ls_result.stdout[:2000])
    print("\n... (显示前2000字符)")