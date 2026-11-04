import ccxt
import pandas as pd
import time
import datetime
import os

# 配置
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
SLEEP_INTERVAL = 5  # 秒，实际部署时可调小

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
    # 取第一档深度
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
    first_write = not os.path.isfile(OUTPUT_FILE)
    columns = ['timestamp', 'datetime', 'exchange', 'symbol',
               'bid_price', 'bid_volume', 'ask_price', 'ask_volume']
    while True:
        records = []
        for name, cfg in EXCHANGES.items():
            try:
                data = fetch_best_bid_ask(cfg['instance'], cfg['symbol'])
                # 转换为可读时间
                data['datetime'] = datetime.datetime.utcfromtimestamp(
                    data['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                records.append(data)
            except Exception as e:
                print(f"[{name}] fetch error: {e}")
        if records:
            df = pd.DataFrame(records, columns=columns)
            if first_write:
                df.to_csv(OUTPUT_FILE, mode='w', index=False, header=True)
                first_write = False
            else:
                df.to_csv(OUTPUT_FILE, mode='a', index=False, header=False)
            print(f"[{datetime.datetime.utcnow()}] 写入 {len(records)} 条记录")
        else:
            print("未获取到任何数据")
        time.sleep(SLEEP_INTERVAL)

if __name__ == '__main__':
    main()