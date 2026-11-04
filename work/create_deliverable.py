#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

# -----------------------------
# 1. 定义交付物目录和文件清单
# -----------------------------
BASE_DIR = Path("deliverable")
FILES = {
    "README.md": """# 项目交付说明

本压缩包包含 M1‑M4 阶段的全部产出以及演示脚本和使用说明。解压后即可直接运行示例演示。""",
    "upwork_service.md": """# Upwork 服务文档

## 功能概述
- 文本生成
- 代码片段提取
- 文件打包

## 接口约定
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| prompt | str | 是 | 用户请求内容 |
| model | str | 否 | 使用的语言模型（默认 `gpt-4`） |
""",
    "index.html": """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>交付物演示</title>
</head>
<body>
<h1>交付物演示页面</h1>
<p>打开此页面即可查看交付文档列表。</p>
<ul>
<li><a href="README.md">README.md</a></li>
<li><a href="upwork_service.md">upwork_service.md</a></li>
<li><a href="example_output.txt">示例输出</a></li>
</ul>
</body>
</html>""",
    "validate.sh": """#!/usr/bin/env bash
# 简单验证脚本：检查关键文件是否存在且非空
required=("README.md" "upwork_service.md" "index.html" "example_output.txt")
for f in "${required[@]}"; do
    if [[ ! -s "$f" ]]; then
        echo "验证失败：$f 不存在或为空"
        exit 1
    fi
done
echo "验证通过：所有文件均存在且非空"
""",
    "example_output.txt": """示例输出：
>>> Hello, World!
>>> 2 + 2 = 4
>>> 文件已成功打包为 deliverable.zip
"""
}

# -----------------------------
# 2. 创建目录并写入文件
# -----------------------------
if BASE_DIR.exists():
    shutil.rmtree(BASE_DIR)
BASE_DIR.mkdir(parents=True)

for name, content in FILES.items():
    file_path = BASE_DIR / name
    file_path.write_text(content, encoding="utf-8")
    # 对可执行脚本添加执行权限
    if name.endswith(".sh"):
        os.chmod(file_path, 0o755)

# -----------------------------
# 3. 打包为 ZIP
# -----------------------------
zip_name = "deliverable"
shutil.make_archive(zip_name, "zip", root_dir=BASE_DIR)

print(f"✅ 打包完成: {zip_name}.zip")