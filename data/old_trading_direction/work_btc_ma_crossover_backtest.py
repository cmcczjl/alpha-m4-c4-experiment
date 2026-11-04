#!/usr/bin/env python3
"""
BTC/USDT Moving‑Average Crossover Back‑Test

Runs a simple long‑only strategy:
- Buy when short‑term MA crosses above long‑term MA
- Sell (close position) when short‑term MA crosses below long‑term MA
- Uses 100% of equity on each trade
- Assumes instant execution at close price

Outputs:
- Number of trades, win rate, total return (%)
- Detailed trade log to data/btc_ma_trades.csv
"""

import os
import ccxt
import pandas as pd
from datetime import datetime
import math

# ----------------- Configuration -----------------
EXCHANGE_ID = 'binance'
SYMBOL = 'BTC/USDT'
TIMEFRAME = '1d'
LIMIT = 365          # days of historical data
SHORT_MA = 10        # short moving average period
LONG_MA = 50         # long moving average period
START_CAPITAL = 1000.0  # USD

# Output files
OUTPUT_DIR = 'data'
TRADE_LOG = os.path.join(OUTPUT_DIR, 'btc_ma_trades.csv')
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def fetch_ohlcv(exchange, symbol, timeframe, limit):
    """
    Fetch OHLCV data and return as Pandas DataFrame.
    """
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('datetime', inplace=True)
    return df

def generate_signals(df, short_period, long_period):
    """
    Generate buy/sell signals based on moving‑average crossovers.
    """
    df['short_ma'] = df['close'].rolling(window=short_period, min_periods=1).mean()
    df['long_ma'] = df['close'].rolling(window=long_period, min_periods=1).mean()
    df['signal'] = 0
    df.loc[df['short_ma'] > df['long_ma'], 'signal'] = 1   # bullish
    df.loc[df['short_ma'] < df['long_ma'], 'signal'] = -1 # bearish
    df['position'] = df['signal'].diff()
    return df

def backtest(df, start_capital):
    """
    Simulate trades and calculate performance metrics.
    """
    capital = start_capital
    position = 0  # 0 = no position, 1 = long
    entry_price = 0.0
    trade_log = []

    for idx, row in df.iterrows():
        if row['position'] == 1 and position == 0:  # Enter long
            # Allocate all capital to BTC
            qty = capital / row['close']
            entry_price = row['close']
            capital = 0.0
            position = 1
            trade_log.append({
                'date': idx,
                'action': 'BUY',
                'price': row['close'],
                'qty': qty,
                'capital': capital
            })
        elif row['position'] == -1 and position == 1:  # Exit long
            # Sell all BTC
            capital = row['close'] * qty
            profit = capital - start_capital
            trade_log.append({
                'date': idx,
                'action': 'SELL',
                'price': row['close'],
                'qty': qty,
                'capital': capital,
                'profit': profit
            })
            position = 0
            qty = 0.0
            entry_price = 0.0

    # If still holding at the end, close position
    if position == 1:
        capital = df.iloc[-1]['close'] * qty
        trade_log.append({
            'date': df.index[-1],
            'action': 'SELL',
            'price': df.iloc[-1]['close'],
            'qty': qty,
            'capital': capital,
            'profit': capital - start_capital
        })
        position = 0

    # Compute metrics
    trades = [t for t in trade_log if t['action'] == 'SELL']
    num_trades = len(trades)
    wins = sum(1 for t in trades if t.get('profit', 0) > 0)
    win_rate = wins / num_trades if num_trades > 0 else 0.0
    total_return = (capital - start_capital) / start_capital * 100 if start_capital > 0 else 0.0

    # Save detailed log
    log_df = pd.DataFrame(trade_log)
    log_df.to_csv(TRADE_LOG, index=False)

    return {
        'num_trades': num_trades,
        'win_rate': win_rate,
        'total_return_pct': total_return,
        'final_capital': capital
    }

def main():
    exchange = ccxt.binance()
    df = fetch_ohlcv(exchange, SYMBOL, TIMEFRAME, LIMIT)
    df = generate_signals(df, SHORT_MA, LONG_MA)
    results = backtest(df, START_CAPITAL)
    print(f"Trades executed: {results['num_trades']}")
    print(f"Win rate: {results['win_rate']*100:.2f}%")
    print(f"Total return: {results['total_return_pct']:.2f}%")
    print(f"Final capital: ${results['final_capital']:.2f}")

if __name__ == "__main__":
    main()