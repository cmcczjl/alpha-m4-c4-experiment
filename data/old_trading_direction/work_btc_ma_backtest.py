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
import numpy as np
from datetime import datetime
import sys
import time

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
    df.drop(columns=['timestamp'], inplace=True)
    return df

def generate_signals(df, short_period, long_period):
    """
    Generate buy/sell signals based on moving‑average crossovers.
    """
    df['short_ma'] = df['close'].rolling(window=short_period, min_periods=1).mean()
    df['long_ma']  = df['close'].rolling(window=long_period, min_periods=1).mean()
    # Signal: 1 when short_ma > long_ma, -1 when short_ma < long_ma
    df['signal'] = np.where(df['short_ma'] > df['long_ma'], 1, -1)
    # Position change: detect crossovers
    df['position'] = df['signal'].diff()
    # position == 2 : short_ma crossed above long_ma -> buy
    # position == -2: short_ma crossed below long_ma -> sell
    return df

def backtest(df):
    """
    Run backtest on the DataFrame with signals.
    """
    capital = START_CAPITAL
    in_position = False
    entry_price = None
    entry_date = None
    trades = []

    for idx, row in df.iterrows():
        pos_change = row['position']
        price = row['close']

        # Buy signal
        if pos_change == 2 and not in_position:
            # Allocate all capital to BTC
            quantity = capital / price
            entry_price = price
            entry_date = idx
            in_position = True

        # Sell signal
        if pos_change == -2 and in_position:
            exit_price = price
            exit_date = idx
            pnl = (exit_price - entry_price) * quantity
            ret_pct = pnl / capital
            capital += pnl  # Update capital
            trade = {
                'entry_date': entry_date,
                'exit_date': exit_date,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'quantity': quantity,
                'pnl': pnl,
                'ret_pct': ret_pct
            }
            trades.append(trade)
            in_position = False
            entry_price = None
            entry_date = None

    # Close any open position at last price
    if in_position:
        exit_price = df.iloc[-1]['close']
        exit_date = df.index[-1]
        pnl = (exit_price - entry_price) * quantity
        ret_pct = pnl / capital
        capital += pnl
        trade = {
            'entry_date': entry_date,
            'exit_date': exit_date,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantity,
            'pnl': pnl,
            'ret_pct': ret_pct
        }
        trades.append(trade)

    # Save trade log
    trade_df = pd.DataFrame(trades)
    trade_df.to_csv(TRADE_LOG, index=False)

    # Summary statistics
    total_trades = len(trades)
    win_trades = sum(1 for t in trades if t['pnl'] > 0)
    win_rate = win_trades / total_trades if total_trades else 0
    total_return_pct = (capital / START_CAPITAL) - 1

    print(f"Total capital: ${capital:,.2f}")
    print(f"Total return: {total_return_pct*100:,.2f}%")
    print(f"Total trades: {total_trades}")
    print(f"Win rate: {win_rate*100:,.2f}%")
    print(f"Trade log saved to {TRADE_LOG}")

def main():
    # Initialize exchange
    exchange = getattr(ccxt, EXCHANGE_ID)({
        'enableRateLimit': True,
    })

    # Fetch data
    print("Fetching OHLCV data...")
    df = fetch_ohlcv(exchange, SYMBOL, TIMEFRAME, LIMIT)
    print(f"Fetched {len(df)} rows.")

    # Generate signals
    print("Generating signals...")
    df = generate_signals(df, SHORT_MA, LONG_MA)

    # Run backtest
    print("Running backtest...")
    backtest(df)

if __name__ == "__main__":
    main()