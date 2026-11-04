#!/bin/bash
# 安装 act 及其环境验证脚本
set -e
echo "正在从 GitHub 下载并安装 act..."
curl -fsSL https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
echo "验证安装结果:"
if command -v act >/dev/null 2>&1; then
    act --version
    echo "act installed successfully"
else
    # 如果不在 PATH 中，尝试查寻默认安装路径
    /usr/local/bin/act --version && echo "act installed successfully at /usr/local/bin/act"
fi