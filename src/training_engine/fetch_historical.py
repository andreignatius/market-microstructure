import ccxt
import pandas as pd
from datetime import datetime, timedelta

# Initialize the exchange
exchange = ccxt.binanceusdm()

# Define the symbol and time range
symbol = 'BTC/USDT'
since = exchange.parse8601((datetime.utcnow() - timedelta(hours=2)).isoformat())

all_trades = []
while since < exchange.milliseconds():
    # Fetch trades with limit
    trades = exchange.fetch_trades(symbol, since=since, limit=500)
    if not trades:
        break
    all_trades.extend(trades)
    since = trades[-1]['timestamp'] + 1  # Move to the next timestamp

# Convert trades to DataFrame
trades_df = pd.DataFrame(all_trades)

# Convert timestamp to datetime
trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'], unit='ms')

# Group into OHLC data
ohlc = trades_df.resample('1s', on='timestamp').agg({
    'price': ['first', 'max', 'min', 'last'],
    'amount': 'sum'
}).dropna()

# Rename columns
ohlc.columns = ['open', 'high', 'low', 'close', 'volume']

# Display OHLC data
print(ohlc)
ohlc.to_csv("ohlc_2hrs.csv")
# # Plot OHLC data
# import matplotlib.pyplot as plt

# fig, ax1 = plt.subplots(figsize=(12, 6))

# # Plot OHLC
# ohlc[['open', 'high', 'low', 'close']].plot(ax=ax1)
# ax1.set_ylabel('Price')
# ax1.set_title(f'OHLC Data for {symbol}')
# ax1.legend(['Open', 'High', 'Low', 'Close'])

# # Plot volume on the secondary y-axis
# ax2 = ax1.twinx()
# ohlc['volume'].plot(kind='bar', ax=ax2, alpha=0.3, color='gray', width=0.03, position=0)
# ax2.set_ylabel('Volume')

# plt.show()
# print()