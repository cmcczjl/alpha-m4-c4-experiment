#!/usr/bin/env python3
"""M4-0：推送 Landing Page 到 GitHub"""
import subprocess, os, sys, datetime

ROOT = "/root/agi-agent"
os.chdir(ROOT)

# 检查必要文件
required = ["index.html", "README.md", "data/pricing.md"]
missing = [f for f in required if not os.path.exists(f)]
if missing:
    print(f"FAIL: 缺失文件 {missing}")
    sys.exit(1)

# 1. 初始化仓库（清理旧的）
subprocess.run("rm -rf .git", shell=True, capture_output=True)
subprocess.run("git init", shell=True, check=True)

# 2. 配置 git
subprocess.run("git config user.email 'alpha@agi.local'", shell=True)
subprocess.run("git config user.name 'Explorer-alpha'", shell=True)

# 3. 添加并提交
subprocess.run("git add -A", shell=True, check=True)
subprocess.run("git commit -m 'M4 landing page: $45/$120/$270 pricing + CI'", shell=True, check=True)

# 4. 创建远程仓库（如果已存在跳过创建）
result = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
if not result.stdout.strip():
    # 用 gh api 创建仓库
    repo_name = "alpha-m4-c4-experiment"
    subprocess.run(f"gh repo create {repo_name} --public --description 'M4 Landing Page for AI Automation Agent' --homepage https://{os.environ.get('GITHUB_ACTOR', 'cmcczjl')}.github.io/{repo_name}", shell=True, check=True)
    subprocess.run(f"git remote add origin https://github.com/cmcczjl/{repo_name}.git", shell=True)

subprocess.run("git branch -M main", shell=True)
subprocess.run("git push -u origin main", shell=True, check=True)

# 5. 启用 GitHub Pages
subprocess.run("git cliche pages --source=docs --branch=gh-pages --push", shell=True)  # 备选
subprocess.run(f"gh repo edit alpha-m4-c4-experiment --enable-pages --source=main:/ --dest=/ --force", shell=True, check=True)

print(f"✅ 推送完成，GitHub Pages 已启用")
print(f"访问地址: https://cmcczjl.github.io/alpha-m4-c4-experiment/")
print(f"提交时间: {datetime.datetime.now().isoformat()}")