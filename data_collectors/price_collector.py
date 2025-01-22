import requests
import pandas as pd
from datetime import datetime, timedelta

def get_crypto_prices(symbol: str, timeframe: str) -> pd.DataFrame:
    """
    Collect cryptocurrency price data from CoinGecko API (Free tier)
    """
    # Map common symbols to CoinGecko IDs
    symbol_map = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'BNB': 'binancecoin',
        'XRP': 'ripple',
        'ADA': 'cardano'
    }

    coin_id = symbol_map.get(symbol.upper(), symbol.lower())

    # CoinGecko free API endpoint (no API key required)
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"

    # Calculate days parameter
    days = '1' if timeframe == "24h" else '7' if timeframe == "7d" else '30'

    params = {
        'vs_currency': 'usd',
        'days': days,
        'interval': 'hourly' if days in ['1', '7'] else 'daily'
    }

    try:
        response = requests.get(url, params=params, headers={'Accept': 'application/json'})

        # Handle rate limiting
        if response.status_code == 429:
            print("CoinGecko API rate limit reached. Please try again in a minute.")
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close'])

        response.raise_for_status()
        data = response.json()

        if 'prices' not in data:
            print(f"Unexpected API response format: {data}")
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close'])

        # Create DataFrame with timestamp and price
        df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Calculate OHLC for each interval
        interval = '1H' if days in ['1', '7'] else '1D'
        ohlc = df.set_index('timestamp').price.resample(interval).ohlc().fillna(method='ffill')
        return ohlc.reset_index()

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("CoinGecko API authentication error. Service might require an API key.")
        else:
            print(f"HTTP error occurred: {e}")
        return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close'])
    except Exception as e:
        print(f"Error fetching price data: {e}")
        return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close'])