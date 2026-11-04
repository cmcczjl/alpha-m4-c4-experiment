#!/usr/bin/env python3
"""
完整的跨平台 BTC 套利监控脚本

- 使用 ccxt 同时连接 Binance (BTC/USDT) 与 Kraken (BTC/USD)。
- 计算买入 Binance、卖出 Kraken（或反向）的净利润。
- 若净利润 ≥ PROFIT_THRESHOLD_USD，则记录到 data/arbitrage_log.csv。
- 脚本一次性运行（可加入 cron / 循环自行扩展）。
"""

import ccxt
import csv
import os
import datetime
from decimal import Decimal, getcontext, ROUND_DOWN

# ------------------- 配置 -------------------
# Decimal 精度
getcontext().prec = 12

# 交易所配置
EXCHANGES = {
    'binance': {
        'instance': ccxt.binance({
            'enableRateLimit': True,
            'options': {'adjustForTimeDifference': True},
        }),
        'symbol': 'BTC/USDT',
        'fee_rate': Decimal('0.0010'),   # 0.10% maker/taker 估算
    },
    'kraken': {
        'instance': ccxt.kraken({
            'enableRateLimit': True,
            'options': {'adjustForTimeDifference': True},
        }),
        'symbol': 'BTC/USD',
        'fee_rate': Decimal('0.0026'),   # 0.26% 现货费率（估算）
    },
}

# 跨平台转账费用（假设一次转账 5 USD）
TRANSFER_FEE_USD = Decimal('5.0')

# 只记录净利润大于此阈值的机会
PROFIT_THRESHOLD_USD = Decimal('10.0')

# 输出目录与文件
OUTPUT_DIR = os.path.join('data')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'arbitrage_log.csv')

# ------------------- 工具函数 -------------------
def ensure_output_dir():
    """确保输出目录存在"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_best_prices(exchange_cfg):
    """
    从指定交易所获取最佳买卖价
    返回 dict: {'bid': Decimal, 'ask': Decimal, 'timestamp': datetime}
    """
    try:
        order_book = exchange_cfg['instance'].fetch_order_book(exchange_cfg['symbol'])
        bid_price = Decimal(str(order_book['bids'][0][0]))  # 最高买价（卖方出价）
        ask_price = Decimal(str(order_book['asks'][0][0]))  # 最低卖价（买方出价）
        return {
            'bid': bid_price,
            'ask': ask_price,
            'timestamp': datetime.datetime.utcnow(),
        }
    except Exception as e:
        print(f"[{exchange_cfg['symbol']}] Error fetching order book: {e}")
        return None

def calculate_spread(buy_ex, sell_ex, buy_price_info, sell_price_info):
    """
    计算买入 (buy_ex) 并卖出 (sell_ex) 的净利润

    参数:
        buy_ex / sell_ex: 交易所键名 ('binance' or 'kraken')
        buy_price_info / sell_price_info: fetch_best_prices 返回值

    返回:
        dict 包含:
            - gross_spread: 卖出价 - 买入价
            - total_fees: 交易费 + 转账费（USD）
            - net_profit_usd: 计算后的净利润（USD）
            - details: 供日志使用的字符串描述
    """
    # 统一计价：假设 USDT 与 USD 1:1
    buy_price = buy_price_info['ask']   # 在买入交易所支付的最低价
    sell_price = sell_price_info['bid'] # 在卖出交易所获得的最高价

    # 交易费用（基于买入/卖出金额）
    buy_fee = buy_price * EXCHANGES[buy_ex]['fee_rate']
    sell_fee = sell_price * EXCHANGES[sell_ex]['fee_rate']

    # 毛利润（卖出价 - 买入价）
    gross_spread = sell_price - buy_price

    # 总费用（买费 + 卖费 + 转账费）
    total_fees = (buy_fee + sell_fee + TRANSFER_FEE_USD).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

    # 净利润（以 USD 计）
    net_profit = (gross_spread - total_fees).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

    details = (
        f"Buy {buy_ex.upper()} @ {buy_price:.2f}, "
        f"Sell {sell_ex.upper()} @ {sell_price:.2f}, "
        f"Gross Spread {gross_spread:.2f}, "
        f"Fees {total_fees:.2f}, Net {net_profit:.2f}"
    )
    return {
        'gross_spread': gross_spread,
        'total_fees': total_fees,
        'net_profit_usd': net_profit,
        'details': details,
    }

def log_opportunity(timestamp, direction, net_profit, details):
    """将符合阈值的套利机会追加写入 CSV"""
    ensure_output_dir()
    file_exists = os.path.isfile(OUTPUT_FILE)
    with open(OUTPUT_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp_utc', 'direction', 'net_profit_usd', 'details'])
        writer.writerow([timestamp.isoformat(), direction, f"{net_profit:.2f}", details])

def main():
    # 获取两家交易所的最新报价
    binance_info = fetch_best_prices(EXCHANGES['binance'])
    kraken_info = fetch_best_prices(EXCHANGES['kraken'])

    if not binance_info or not kraken_info:
        print("Failed to fetch order books from both exchanges.")
        return

    # 方向1：在 Binance 买入、在 Kraken 卖出
    spread1 = calculate_spread('binance', 'kraken', binance_info, kraken_info)
    # 方向2：在 Kraken 买入、在 Binance 卖出
    spread2 = calculate_spread('kraken', 'binance', kraken_info, binance_info)

    now = datetime.datetime.utcnow()

    # 检查并记录符合阈值的机会
    if spread1['net_profit_usd'] >= PROFIT_THRESHOLD_USD:
        log_opportunity(now, 'BINANCE->KRAKEN', spread1['net_profit_usd'], spread1['details'])
        print(f"[OPPORTUNITY] {now} BINANCE->KRAKEN Net ${spread1['net_profit_usd']}: {spread1['details']}")
    else:
        print(f"[INFO] BINANCE->KRAKEN net profit ${spread1['net_profit_usd']} below threshold.")

    if spread2['net_profit_usd'] >= PROFIT_THRESHOLD_USD:
        log_opportunity(now, 'KRAKEN->BINANCE', spread2['net_profit_usd'], spread2['details'])
        print(f"[OPPORTUNITY] {now} KRAKEN->BINANCE Net ${spread2['net_profit_usd']}: {spread2['details']}")
    else:
        print(f"[INFO] KRAKEN->BINANCE net profit ${spread2['net_profit_usd']} below threshold.")

if __name__ == "__main__":
    main()

[FILE]
knowledge/research_arbitrage.md