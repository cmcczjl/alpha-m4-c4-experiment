#!/usr/bin/env bash
# 简单验证脚本：检查关键文件是否存在且非空
required=("README.md" "upwork_service.md" "index.html" "example_output.txt")
for f in "${required[@]}"; do
    if [[ ! -s "$f" ]]; then
        echo "验证失败：$f 不存在或为空"
        exit 1
    fi
done
echo "验证通过：所有文件均存在且非空"
