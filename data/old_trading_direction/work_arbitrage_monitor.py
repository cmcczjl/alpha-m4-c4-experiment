#!/usr/bin/env python3
"""
Arbitrage monitor between Binance and Kraken for BTC.
Fetches order books, calculates net profit after fees and transfer costs,
and logs profitable opportunities (> PROFIT_THRESHOLD_USD) to a CSV file.
"""

import ccxt
import csv
import os
import time
import datetime
from decimal import Decimal, ROUND_DOWN, getcontext

# ------------------- 配置 -------------------
# 设置 Decimal 精度
getcontext().prec = 12

# 统一计价：Kraken 返回 USD，Binance 返回 USDT（假设 1:1）
TRANSFER_FEE_USD = Decimal('5.0')   # 假设一次跨平台转账费用（USD）
PROFIT_THRESHOLD_USD = Decimal('10.0')  # 仅记录净利润 > $10 的机会

OUTPUT_DIR = 'data'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'arbitrage_log.csv')

EXCHANGES = {
    'binance': {
        'instance': ccxt.binance({
            'enableRateLimit': True,
            'options': {'adjustForTimeDifference': True},
        }),
        'symbol': 'BTC/USDT',
        'fee_rate': Decimal('0.0010'),  # 0.10% maker/taker 估算
    },
    'kraken': {
        'instance': ccxt.kraken({
            'enableRateLimit': True,
            'options': {'adjustForTimeDifference': True},
        }),
        'symbol': 'BTC/USD',
        'fee_rate': Decimal('0.0026'),  # Kraken 现货约 0.26%
    },
}

# ------------------- 工具函数 -------------------
def fetch_best_prices(exchange_cfg):
    """
    从指定交易所获取最佳买卖价
    """
    try:
        order_book = exchange_cfg['instance'].fetch_order_book(exchange_cfg['symbol'])
        bid_price = Decimal(str(order_book['bids'][0][0]))  # 最高买价
        ask_price = Decimal(str(order_book['asks'][0][0]))  # 最低卖价
        return {
            'bid': bid_price,
            'ask': ask_price,
            'timestamp': datetime.datetime.utcnow(),
        }
    except Exception as e:
        print(f"[{exchange_cfg['symbol']}] Error fetching order book: {e}")
        return None

def calculate_net_profit(buy_exchange, sell_exchange):
    """
    计算在买入方买入、卖出方卖出的净利润（USD）
    """
    # 买入价格（支付给买方）
    buy_price = buy_exchange['ask']  # 低价
    # 卖出价格（收到的价格）
    sell_price = sell_exchange['bid']  # 高价

    # 费用
    buy_fee_rate = EXCHANGES[buy_exchange['symbol'].split('/')[0]]['fee_rate']
    sell_fee_rate = EXCHANGES[sell_exchange['symbol'].split('/')[0]]['fee_rate']
    buy_fee = buy_price * buy_fee_rate
    sell_fee = sell_price * sell_fee_rate

    # 计算净利润
    gross_profit = sell_price - buy_price
    total_fees = buy_fee + sell_fee
    net_profit = gross_profit - total_fees - TRANSFER_FEE_USD

    return {
        'gross_profit': gross_profit,
        'total_fees': total_fees,
        'net_profit': net_profit,
        'buy_price': buy_price,
        'sell_price': sell_price,
        'timestamp': datetime.datetime.utcnow(),
    }

def log_opportunity(log_entry):
    """
    将套利机会写入 CSV
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    header = [
        'timestamp',
        'buy_exchange',
        'sell_exchange',
        'buy_price',
        'sell_price',
        'gross_profit',
        'total_fees',
        'net_profit',
    ]
    file_exists = os.path.isfile(OUTPUT_FILE)
    with open(OUTPUT_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if not file_exists:
            writer.writeheader()
        writer.writerow(log_entry)

def main_loop(interval_seconds=10):
    """
    主循环：持续监控并记录套利机会
    """
    print("Starting arbitrage monitor...")
    while True:
        try:
            # 获取两边的最佳价
            binance_prices = fetch_best_prices(EXCHANGES['binance'])
            kraken_prices = fetch_best_prices(EXCHANGES['kraken'])
            if not binance_prices or not kraken_prices:
                raise RuntimeError("Failed to fetch prices from both exchanges")

            # 1. 先在 Binance 买，在 Kraken 卖
            result1 = calculate_net_profit(
                buy_exchange={'symbol': 'BTC/USDT', 'ask': binance_prices['ask']},
                sell_exchange={'symbol': 'BTC/USD', 'bid': kraken_prices['bid']}
            )
            # 2. 先在 Kraken 买，在 Binance 卖
            result2 = calculate_net_profit(
                buy_exchange={'symbol': 'BTC/USD', 'ask': kraken_prices['ask']},
                sell_exchange={'symbol': 'BTC/USDT', 'bid': binance_prices['bid']}
            )

            # 记录最优的机会
            if result1['net_profit'] > PROFIT_THRESHOLD_USD:
                log_entry = {
                    'timestamp': result1['timestamp'].isoformat(),
                    'buy_exchange': 'Binance',
                    'sell_exchange': 'Kraken',
                    'buy_price': str(result1['buy_price']),
                    'sell_price': str(result1['sell_price']),
                    'gross_profit': str(result1['gross_profit']),
                    'total_fees': str(result1['total_fees']),
                    'net_profit': str(result1['net_profit']),
                }
                log_opportunity(log_entry)
                print(f"[{log_entry['timestamp']}] Opportunity: Binance→Kraken, Net Profit: ${log_entry['net_profit']}")

            if result2['net_profit'] > PROFIT_THRESHOLD_USD:
                log_entry = {
                    'timestamp': result2['timestamp'].isoformat(),
                    'buy_exchange': 'Kraken',
                    'sell_exchange': 'Binance',
                    'buy_price': str(result2['buy_price']),
                    'sell_price': str(result2['sell_price']),
                    'gross_profit': str(result2['gross_profit']),
                    'total_fees': str(result2['total_fees']),
                    'net_profit': str(result2['net_profit']),
                }
                log_opportunity(log_entry)
                print(f"[{log_entry['timestamp']}] Opportunity: Kraken→Binance, Net Profit: ${log_entry['net_profit']}")

        except Exception as e:
            print(f"[ERROR] {e}")

        time.sleep(interval_seconds)

if __name__ == "__main__":
    main_loop()