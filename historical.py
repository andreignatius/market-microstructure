import ccxt
import pandas as pd
import datetime
import time

# Initialize the Binance exchange
exchange = ccxt.binance({
    'rateLimit': 1200,
    'enableRateLimit': True,
})

def fetch_binance_ohlcv(symbol, timeframe, since, limit=500):
    all_data = []
    while True:
        data = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
        if len(data) == 0:
            break
        all_data += data
        since = data[-1][0] + 1
        time.sleep(exchange.rateLimit / 1000)
        if len(data) < limit:
            break
    return all_data

# Parameters
symbol = 'BTC/USDT'
timeframe = '1m'  # 1-minute granularity
since = exchange.parse8601('2024-04-14T00:00:00Z')  # Start date

data = fetch_binance_ohlcv(symbol, timeframe, since)

# Convert to DataFrame
columns = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
df = pd.DataFrame(data, columns=columns)

# Convert timestamp to datetime
df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')

# Save to CSV
df.to_csv('binance_btcusdt_1min_ccxt.csv', index=False)

print("Data saved to binance_btcusdt_1min_ccxt.csv")
