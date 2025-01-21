import requests
import pandas as pd
from datetime import datetime, timedelta

def get_crypto_prices(symbol: str, timeframe: str) -> pd.DataFrame:
    """
    Collect cryptocurrency price data from CoinGecko API
    """
    # Calculate time range
    end_time = datetime.now()
    if timeframe == "24h":
        start_time = end_time - timedelta(days=1)
    elif timeframe == "7d":
        start_time = end_time - timedelta(days=7)
    else:
        start_time = end_time - timedelta(days=30)

    # CoinGecko API endpoint
    url = f"https://api.coingecko.com/api/v3/coins/{symbol.lower()}/market_chart"
    params = {
        'vs_currency': 'usd',
        'from': int(start_time.timestamp()),
        'to': int(end_time.timestamp()),
        'interval': 'hourly'
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        # Convert to DataFrame
        df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Calculate OHLC
        ohlc = df.set_index('timestamp').price.resample('1H').ohlc()
        return ohlc.reset_index()

    except Exception as e:
        print(f"Error fetching price data: {e}")
        return pd.DataFrame()
