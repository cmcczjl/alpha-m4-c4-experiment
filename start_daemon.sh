#!/bin/bash
# 探索者-α 启动脚本
cd /root/agi-agent
nohup python3 run_autonomous.py >> logs/daemon.log 2>&1 &
echo "探索者-α 已启动，PID: $!"
