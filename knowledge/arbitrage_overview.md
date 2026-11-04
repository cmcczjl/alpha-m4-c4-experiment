# 套利概览

## 什么是跨交易所套利？

跨交易所套利（Cross‑Exchange Arbitrage）指在同一时间点上，利用不同交易所之间同一标的资产（如 BTC/USDT）报价的差异，低买高卖，从价差中获利。  
典型流程：

1. **获取实时买卖价**：从两个或多个交易所获取最优买价（Bid）和卖价（Ask）。
2. **计算价差**：  
   - 若 `Exchange A` 的 **Ask** 低于 `Exchange B` 的 **Bid**，则可以在 A 买入、在 B 卖出。  
   - 价差 = `Bid_B` - `Ask_A`.
3. **扣除费用**：考虑交易手续费、提现/转账费用以及网络延迟。只有当 **净价差 > 费用** 时才值得执行。
4. **执行**：通过 API 下单并在必要时转移资产（如跨链或跨平台转账）。

## 关键要点

| 要素 | 说明 |
|------|------|
| **交易所选择** | 需选流动性高、API 稳定、提现速度快的交易所（如 Binance、Kraken）。 |
| **手续费** | 现货交易一般为 0.1%~0.2%（maker/taker），提现费用视链而定。 |
| **延迟** | 价格快速变动，网络与下单延迟会导致套利机会消失。 |
| **资金分配** | 为避免转账时间成本，通常在每个交易所预留一定余额。 |
| **风险** | 市场波动、API 失效、提现冻结、对手方信用风险。 |

## 初步实现思路（Python + ccxt）

1. **配置交易所**：使用 `ccxt` 实例化 Binance 与 Kraken，设定交易对 `BTC/USDT`（Kraken 为 `BTC/USD`，需统一计价单位）。
2. **获取订单薄**：调用 `fetch_order_book`，提取最高买价 (`bid_price`) 与最低卖价 (`ask_price`)。
3. **计算套利**：  
   ```python
   spread = bid_kraken - ask_binance
   net_profit = spread - (fee_binance + fee_kraken + transfer_fee)
   ```
4. **阈值检测**：若 `net_profit` 大于设定阈值（如 0.2%），记录并发送信号（可写入 CSV 或推送到 Telegram）。
5. **循环监控**：每隔几秒执行一次，持续捕捉瞬时机会。

## 下一步

- 编写监控脚本 `work/arbitrage_monitor.py`，实现上述功能并输出 CSV 报告。  
- 运行脚本，验证是否能实时捕获正向价差。  
- 根据实际结果评估手续费与转账成本，调整阈值。

[FILE]
work/arbitrage_monitor.py