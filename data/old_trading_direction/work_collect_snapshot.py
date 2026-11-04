import ccxt
import csv
import os
import time
import datetime

# ------------------- 配置 -------------------
EXCHANGES = {
    'binance': {
        'instance': ccxt.binance(),
        'symbol': 'BTC/USDT',
    },
    'kraken': {
        'instance': ccxt.kraken(),
        'symbol': 'BTC/USD',
    },
}
OUTPUT_DIR = 'data'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'price_snapshot.csv')
# ------------------------------------------------

def ensure_output_dir():
    if not os.path.isdir(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_best_bid_ask(exchange, symbol):
    """
    返回 dict:
    {
        'timestamp': int,
        'exchange': str,
        'symbol': str,
        'bid_price': float,
        'bid_volume': float,
        'ask_price': float,
        'ask_volume': float,
    }
    """
    order_book = exchange.fetch_order_book(symbol)
    best_bid = order_book['bids'][0] if order_book['bids'] else (None, None)
    best_ask = order_book['asks'][0] if order_book['asks'] else (None, None)
    return {
        'timestamp': int(time.time() * 1000),
        'exchange': exchange.id,
        'symbol': symbol,
        'bid_price': best_bid[0],
        'bid_volume': best_bid[1],
        'ask_price': best_ask[0],
        'ask_volume': best_ask[1],
    }

def main():
    ensure_output_dir()
    # 如果文件不存在，写入表头
    file_exists = os.path.isfile(OUTPUT_FILE)
    fieldnames = ['timestamp', 'datetime', 'exchange', 'symbol',
                  'bid_price', 'bid_volume', 'ask_price', 'ask_volume']
    with open(OUTPUT_FILE, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for name, cfg in EXCHANGES.items():
            try:
                data = fetch_best_bid_ask(cfg['instance'], cfg['symbol'])
                data['datetime'] = datetime.datetime.utcfromtimestamp(
                    data['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                writer.writerow(data)
                print(f"[{name}] bid {data['bid_price']} ask {data['ask_price']}")
            except Exception as e:
                print(f"[{name}] fetch error: {e}")

if __name__ == "__main__":
    main()