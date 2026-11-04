#!/usr/bin/env bash
# 创建日志目录（如果不存在）
mkdir -p logs

# 执行下载描述脚本并记录日志
bash view_download_desc.sh > logs/download.log 2>&1

# 输出日志内容以供检查
cat logs/download.log