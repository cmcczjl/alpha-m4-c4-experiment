# 探索者-α 启动指南

## 当前状态
- **进程**: 运行中 (PID: 1318240)
- **目标**: 赚钱。没有金额限制，没有时间限制。
- **频率**: 每30分钟自主探索一轮
- **位置**: `/root/agi-agent/`

## 今日产出 (2026-10-27)

### work/ 目录
| 文件 | 大小 | 说明 |
|------|------|------|
| fetch_price.py | 2.5KB | CCXT 多交易所价格抓取 |
| collect_snapshot.py | 2.3KB | 订单薄快照收集 |
| arbitrage_monitor.py | 6.1KB | 套利监控器 |

### data/knowledge/ 目录
| 文件 | 大小 | 说明 |
|------|------|------|
| market_microstructure.md | 421B | 市场微观结构 |
| risk_management.md | 687B | 风险管理 |
| statistical_inference.md | 646B | 统计推断 |

### data/journal/
- **2026-10-27.md**: 466行探索日志

## 使用方法

### 查看状态
```bash
tail -20 /root/agi-agent/data/20261027.log
```

### 停止进程
```bash
pkill -f run_autonomous.py
```

### 重启
```bash
cd /root/agi-agent && python3 run_autonomous.py
```

### 配置飞书（明天）
1. 更新 `config.yaml` 中的飞书配置
2. 运行 `python3 run.py --mode both`

## 注意事项
- 进程会持续运行，直到被手动停止
- 所有日志保存在 `data/20261027.log`
- 工作文件保存在 `work/` 和 `data/knowledge/`
- 备份位于 `/root/agi-agent-backup-20261027_1730/`
