#!/bin/bash
# 探索者-α 看门狗：保持 autonomous 和 feishu_bot 存活，崩溃自动重启
cd /root/agi-agent || exit 1

ensure_autonomous() {
    if ! pgrep -f 'run_autonomous.py' > /dev/null 2>&1; then
        echo "[$(date '+%F %T')] autonomous 未运行，启动中..." >> logs/supervisor.log
        python3 run_autonomous.py >> logs/autonomous.log 2>&1 &
    fi
}

ensure_bot() {
    if ! pgrep -f 'feishu_bot.py' > /dev/null 2>&1; then
        echo "[$(date '+%F %T')] feishu_bot 未运行，启动中..." >> logs/supervisor.log
        python3 feishu_bot.py >> logs/feishu_bot.log 2>&1 &
    fi
}

while true; do
    ensure_autonomous
    ensure_bot
    sleep 60
done
