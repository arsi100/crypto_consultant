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
        interval = 'hourly'
    elif timeframe == "7d":
        start_time = end_time - timedelta(days=7)
        interval = 'hourly'
    else:  # 30d
        start_time = end_time - timedelta(days=30)
        interval = 'daily'

    # Map common symbols to CoinGecko IDs
    symbol_map = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'BNB': 'binancecoin',
        'XRP': 'ripple',
        'ADA': 'cardano'
    }

    coin_id = symbol_map.get(symbol.upper(), symbol.lower())

    # CoinGecko API endpoint
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': 'usd',
        'days': '1' if timeframe == "24h" else '7' if timeframe == "7d" else '30',
        'interval': interval
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for bad status codes
        data = response.json()

        if 'prices' not in data:
            print(f"Unexpected API response format: {data}")
            return pd.DataFrame()

        # Create DataFrame with timestamp and price
        df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Calculate OHLC for each interval
        ohlc = df.set_index('timestamp').price.resample('1H').ohlc().fillna(method='ffill')
        return ohlc.reset_index()

    except Exception as e:
        print(f"Error fetching price data: {e}")
        return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close'])