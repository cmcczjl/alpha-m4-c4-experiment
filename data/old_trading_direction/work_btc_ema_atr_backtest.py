#!/usr/bin/env python3
"""
BTC/USDT EMA + ATR Back‑Test

Strategy:
- EMA 10 vs EMA 50 crossover for entry.
- 100% of equity used on each trade.
- Stop‑loss = 1.5 * ATR(14) below entry price.
- Take‑profit = 3.0 * ATR(14) above entry price.
- No short positions (long‑only).
- Assumes instant execution at close price.

Outputs:
- trade_log.csv: detailed trade info.
- summary.txt: number of trades, win rate, total return (%), max drawdown (%).

Author: 探索者-α
"""

import os
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime

# ----------------- Configuration -----------------
EXCHANGE_ID = 'binance'
SYMBOL = 'BTC/USDT'
TIMEFRAME = '1d'
LIMIT = 1000          # days of historical data (more than 365 for safety)
SHORT_EMA = 10
LONG_EMA = 50
ATR_PERIOD = 14
SL_MULT = 1.5
TP_MULT = 3.0
START_CAPITAL = 1000.0

OUTPUT_DIR = 'data'
TRADE_LOG = os.path.join(OUTPUT_DIR, 'btc_ema_atr_trades.csv')
SUMMARY_FILE = os.path.join(OUTPUT_DIR, 'btc_ema_atr_summary.txt')

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# ----------------- Data Fetching -----------------
def fetch_ohlcv(exchange, symbol, timeframe, limit):
    """Fetch OHLCV data and return as Pandas DataFrame."""
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('datetime', inplace=True)
    df.drop(columns=['timestamp'], inplace=True)
    return df

# ----------------- Indicator Calculation -----------------
def add_indicators(df):
    df['ema_short'] = df['close'].ewm(span=SHORT_EMA, adjust=False).mean()
    df['ema_long']  = df['close'].ewm(span=LONG_EMA, adjust=False).mean()
    df['atr'] = df['high'].rolling(window=ATR_PERIOD).max() - df['low'].rolling(window=ATR_PERIOD).min()
    # Signal: 1 when ema_short > ema_long, -1 when ema_short < ema_long
    df['signal'] = np.where(df['ema_short'] > df['ema_long'], 1, -1)
    # Forward fill to avoid NaN at start
    df['signal'].fillna(0, inplace=True)

# ----------------- Backtesting -----------------
def backtest(df):
    equity = START_CAPITAL
    position = 0          # 0 = flat, 1 = long
    entry_price = 0.0
    stop_price = 0.0
    target_price = 0.0
    trade_log = []

    for i in range(1, len(df)):
        today = df.iloc[i]
        yesterday = df.iloc[i-1]

        # Check for entry
        if position == 0 and yesterday['signal'] <= 0 and today['signal'] > 0:
            # Long entry
            entry_price = today['close']
            atr = today['atr']
            stop_price = entry_price - SL_MULT * atr
            target_price = entry_price + TP_MULT * atr
            position = 1
            trade_entry_time = today.name
            # No immediate exit on same day (unless price hits SL/TP)
            continue

        # If in position, check for exit conditions
        if position == 1:
            # Check stop loss hit
            if today['low'] <= stop_price:
                exit_price = stop_price
                pnl = (exit_price - entry_price) * (equity / entry_price)
                equity += pnl
                trade_log.append({
                    'entry_time': trade_entry_time,
                    'exit_time': today.name,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'return_pct': pnl / equity,
                    'type': 'SL'
                })
                position = 0
                continue

            # Check take profit hit
            if today['high'] >= target_price:
                exit_price = target_price
                pnl = (exit_price - entry_price) * (equity / entry_price)
                equity += pnl
                trade_log.append({
                    'entry_time': trade_entry_time,
                    'exit_time': today.name,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'return_pct': pnl / equity,
                    'type': 'TP'
                })
                position = 0
                continue

            # Check for exit on next signal crossover (cross below)
            if yesterday['signal'] >= 0 and today['signal'] < 0:
                exit_price = today['close']
                pnl = (exit_price - entry_price) * (equity / entry_price)
                equity += pnl
                trade_log.append({
                    'entry_time': trade_entry_time,
                    'exit_time': today.name,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'return_pct': pnl / equity,
                    'type': 'Crossover'
                })
                position = 0
                continue

    # If still in position at end of data, close at last close price
    if position == 1:
        exit_price = df.iloc[-1]['close']
        pnl = (exit_price - entry_price) * (equity / entry_price)
        equity += pnl
        trade_log.append({
            'entry_time': trade_entry_time,
            'exit_time': df.index[-1],
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'return_pct': pnl / equity,
            'type': 'End'
        })
        position = 0

    # Convert to DataFrame
    trade_df = pd.DataFrame(trade_log)
    return trade_df, equity

# ----------------- Summary Metrics -----------------
def compute_summary(trade_df, final_equity):
    total_trades = len(trade_df)
    wins = trade_df[trade_df['pnl'] > 0].shape[0]
    win_rate = wins / total_trades if total_trades > 0 else 0
    total_return_pct = (final_equity - START_CAPITAL) / START_CAPITAL * 100

    # Max drawdown calculation
    equity_curve = [START_CAPITAL]
    for idx, row in trade_df.iterrows():
        equity_curve.append(equity_curve[-1] + row['pnl'])
    equity_curve = pd.Series(equity_curve)
    peak = equity_curve.expanding(min_periods=1).max()
    drawdown = (equity_curve - peak) / peak
    max_drawdown_pct = drawdown.min() * 100

    summary = {
        'total_trades': total_trades,
        'win_rate': win_rate,
        'total_return_pct': total_return_pct,
        'max_drawdown_pct': max_drawdown_pct
    }
    return summary

# ----------------- Main -----------------
def main():
    exchange = getattr(ccxt, EXCHANGE_ID)()
    df = fetch_ohlcv(exchange, SYMBOL, TIMEFRAME, LIMIT)
    add_indicators(df)

    trade_df, final_equity = backtest(df)

    # Save trade log
    trade_df.to_csv(TRADE_LOG, index=False)

    # Compute and save summary
    summary = compute_summary(trade_df, final_equity)
    with open(SUMMARY_FILE, 'w') as f:
        f.write(f"Total Trades: {summary['total_trades']}\n")
        f.write(f"Win Rate: {summary['win_rate']*100:.2f}%\n")
        f.write(f"Total Return: {summary['total_return_pct']:.2f}%\n")
        f.write(f"Max Drawdown: {summary['max_drawdown_pct']:.2f}%\n")

    print(f"Backtest completed. Final equity: ${final_equity:.2f}")
    print(f"Summary written to {SUMMARY_FILE}")
    print(f"Trade log written to {TRADE_LOG}")

if __name__ == "__main__":
    main()