import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta
import os

# Binance exchange setup
exchange = ccxt.binance({'enableRateLimit': True})

symbol = 'DOGE/USDT'
timeframe = '1m'

# Set date range (last 1 year from today)
end_date = datetime.utcnow()
start_date = end_date - timedelta(days=365)

since = int(exchange.parse8601(start_date.strftime('%Y-%m-%dT%H:%M:%S')))

ohlcv_data = []

while since < exchange.milliseconds():
    print(f'Fetching data since {exchange.iso8601(since)}')

    data = exchange.fetch_ohlcv(symbol, timeframe, since, limit=1000)

    if not data:
        break

    ohlcv_data += data
    since = data[-1][0] + 60000  # move by 1 minute

    # Respect Binance rate limits
    time.sleep(exchange.rateLimit / 1000)

# Create DataFrame
df = pd.DataFrame(ohlcv_data, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
df['Time'] = pd.to_datetime(df['Time'], unit='ms')

# Save to Render persistent disk
output_folder = '/data'
os.makedirs(output_folder, exist_ok=True)
output_file = os.path.join(output_folder, 'dogeusdt_1m_last_year.csv')

df.to_csv(output_file, index=False)
print(f'Data saved successfully: {output_file}')
