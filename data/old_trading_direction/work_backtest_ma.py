#!/usr/bin/env python3
import ccxt
import pandas as pd
import datetime
import os
import json

# ------------------------------
# 配置
# ------------------------------
EXCHANGE = 'binance'
SYMBOL = 'BTC/USDT'
TIMEFRAME = '1d'
LIMIT = 365 * 3            # 最近 3 年日线
START_BALANCE = 1000.0
POSITION_SIZE = 0.10       # 每笔使用 10% 账户余额
TRADING_FEE = 0.001         # 0.1% 进出场手续费
TAKE_PROFIT = 0.02          # 2% 止盈
STOP_LOSS = 0.04            # 4% 止损
OUTPUT_DIR = 'results'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------------------------
# 数据获取
# ------------------------------
def fetch_data():
    exchange = getattr(ccxt, EXCHANGE)({'enableRateLimit': True})
    # 取足够久的数据，确保能算出 50 日 SMA
    since = exchange.parse8601(
        (datetime.datetime.utcnow() - datetime.timedelta(days=LIMIT * 2)).isoformat()
    )
    bars = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, since=since, limit=LIMIT)
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('date', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']]
    return df

# ------------------------------
# SMA 计算
# ------------------------------
def add_sma(df):
    df['sma20'] = df['close'].rolling(window=20).mean()
    df['sma50'] = df['close'].rolling(window=50).mean()
    df.dropna(inplace=True)   # 去除前期 NaN
    return df

# ------------------------------
# 交易信号与回测
# ------------------------------
def run_backtest(df):
    balance = START_BALANCE
    equity_curve = []          # 每日权益（仅记录 cash，未计入未实现盈亏）
    trades = []                # 记录每笔交易

    position = None            # None / 'long' / 'short'
    entry_price = None
    btc_amount = None
    entry_index = None

    # 为了判断交叉，需要前一根K线的 SMA
    df['sma20_prev'] = df['sma20'].shift(1)
    df['sma50_prev'] = df['sma50'].shift(1)

    for idx, row in df.iterrows():
        # 记录当日权益（仅现金）
        equity_curve.append({'date': idx.isoformat(), 'balance': balance})

        # 若已有持仓，先检查止盈/止损
        if position is not None:
            price = row['close']
            if position == 'long':
                if price >= entry_price * (1 + TAKE_PROFIT):
                    # 止盈平仓
                    exit_price = price
                    profit_factor = (exit_price / entry_price) - 1
                elif price <= entry_price * (1 - STOP_LOSS):
                    # 止损平仓
                    exit_price = price
                    profit_factor = (exit_price / entry_price) - 1
                else:
                    exit_price = None
                if exit_price is not None:
                    # 计算平仓
                    position_value = btc_amount * exit_price
                    fee_exit = position_value * TRADING_FEE
                    balance += position_value - fee_exit
                    trades.append({
                        'entry_date': entry_index.isoformat(),
                        'exit_date': idx.isoformat(),
                        'side': 'long',
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'btc_amount': btc_amount,
                        'profit_usd': position_value - (btc_amount * entry_price) - fee_exit,
                        'profit_pct': profit_factor * 100
                    })
                    position = None
                    entry_price = None
                    btc_amount = None
                    entry_index = None
                    continue  # 本日已平仓，进入下一根K线

            elif position == 'short':
                if price <= entry_price * (1 - TAKE_PROFIT):
                    # 止盈平仓（做空盈利）
                    exit_price = price
                    profit_factor = (entry_price / exit_price) - 1
                elif price >= entry_price * (1 + STOP_LOSS):
                    # 止损平仓
                    exit_price = price
                    profit_factor = (entry_price / exit_price) - 1
                else:
                    exit_price = None
                if exit_price is not None:
                    # 计算平仓
                    position_value = btc_amount * exit_price
                    fee_exit = position_value * TRADING_FEE
                    # 对于做空，我们在开仓时已获得 (entry_price * btc_amount) 现金
                    # 这里需要把平仓时买回的现金扣除
                    balance += (btc_amount * entry_price) - position_value - fee_exit
                    trades.append({
                        'entry_date': entry_index.isoformat(),
                        'exit_date': idx.isoformat(),
                        'side': 'short',
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'btc_amount': btc_amount,
                        'profit_usd': (btc_amount * entry_price) - position_value - fee_exit,
                        'profit_pct': profit_factor * 100
                    })
                    position = None
                    entry_price = None
                    btc_amount = None
                    entry_index = None
                    continue  # 本日已平仓，进入下一根K线

        # 若当前无持仓，检测 SMA 交叉信号
        if position is None:
            # 20 上穿 50 => 多头信号
            if (row['sma20_prev'] < row['sma50_prev']) and (row['sma20'] >= row['sma50']):
                # 开多仓
                alloc = balance * POSITION_SIZE
                entry_price = row['close']
                btc_amount = alloc / entry_price
                fee_entry = alloc * TRADING_FEE
                balance -= fee_entry  # 只扣除手续费，仓位资金仍视为在余额中（后续平仓时回收）
                position = 'long'
                entry_index = idx
            # 20 下穿 50 => 空头信号
            elif (row['sma20_prev'] > row['sma50_prev']) and (row['sma20'] <= row['sma50']):
                # 开空仓
                alloc = balance * POSITION_SIZE
                entry_price = row['close']
                btc_amount = alloc / entry_price
                fee_entry = alloc * TRADING_FEE
                balance -= fee_entry
                # 对于做空，先把等值的美元锁定（已在 balance 中），不需要额外扣除
                position = 'short'
                entry_index = idx

    # 回测结束后，如果还有未平仓的持仓，强制在最后一天收盘价平仓
    if position is not None:
        final_price = df.iloc[-1]['close']
        idx = df.index[-1]
        if position == 'long':
            exit_price = final_price
            profit_factor = (exit_price / entry_price) - 1
            position_value = btc_amount * exit_price
            fee_exit = position_value * TRADING_FEE
            balance += position_value - fee_exit
            trades.append({
                'entry_date': entry_index.isoformat(),
                'exit_date': idx.isoformat(),
                'side': 'long',
                'entry_price': entry_price,
                'exit_price': exit_price,
                'btc_amount': btc_amount,
                'profit_usd': position_value - (btc_amount * entry_price) - fee_exit,
                'profit_pct': profit_factor * 100
            })
        else:  # short
            exit_price = final_price
            profit_factor = (entry_price / exit_price) - 1
            position_value = btc_amount * exit_price
            fee_exit = position_value * TRADING_FEE
            balance += (btc_amount * entry_price) - position_value - fee_exit
            trades.append({
                'entry_date': entry_index.isoformat(),
                'exit_date': idx.isoformat(),
                'side': 'short',
                'entry_price': entry_price,
                'exit_price': exit_price,
                'btc_amount': btc_amount,
                'profit_usd': (btc_amount * entry_price) - position_value - fee_exit,
                'profit_pct': profit_factor * 100
            })
        position = None

    # 保存结果
    pd.DataFrame(equity_curve).to_csv(os.path.join(OUTPUT_DIR, 'equity_curve.csv'), index=False)
    pd.DataFrame(trades).to_csv(os.path.join(OUTPUT_DIR, 'trades.csv'), index=False)
    summary = {
        'starting_balance': START_BALANCE,
        'ending_balance': round(balance, 2),
        'total_trades': len(trades),
        'net_profit_usd': round(balance - START_BALANCE, 2),
        'net_profit_pct': round((balance - START_BALANCE) / START_BALANCE * 100, 2)
    }
    with open(os.path.join(OUTPUT_DIR, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=4)
    print("回测完成，结果已保存至", OUTPUT_DIR)
    print(json.dumps(summary, indent=4))

def main():
    df = fetch_data()
    df = add_sma(df)
    run_backtest(df)

if __name__ == '__main__':
    main()