import requests
import pandas as pd
import time
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
    base_url = "https://api.coingecko.com/api/v3"

    # Calculate days parameter
    days = '1' if timeframe == "24h" else '7' if timeframe == "7d" else '30'

    params = {
        'vs_currency': 'usd',
        'days': days,
        'interval': 'hourly' if days in ['1', '7'] else 'daily'
    }

    headers = {
        'Accept': 'application/json',
        'User-Agent': 'CryptoAssistant/1.0 PriceCollector'
    }

    # Try up to 3 times with exponential backoff
    max_retries = 3
    retry_delay = 5  # Initial delay in seconds

    for attempt in range(max_retries):
        try:
            # Check API status first
            ping_response = requests.get(
                f"{base_url}/ping",
                headers=headers,
                timeout=5
            )
            if ping_response.status_code != 200:
                print("CoinGecko API is not responding")
                return pd.DataFrame()

            # Get price data
            print(f"Fetching price data for {coin_id}, attempt {attempt + 1}/{max_retries}")
            response = requests.get(
                f"{base_url}/coins/{coin_id}/market_chart",
                params=params,
                headers=headers,
                timeout=10
            )

            if response.status_code == 429:
                wait_time = retry_delay * (2 ** attempt)
                print(f"Rate limited, waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            data = response.json()

            if 'prices' not in data:
                print("No price data available")
                return pd.DataFrame()

            # Create DataFrame with timestamp and price
            df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            # Calculate OHLC for each interval
            interval = '1H' if days in ['1', '7'] else '1D'
            ohlc = df.set_index('timestamp').price.resample(interval).ohlc().fillna(method='ffill')

            print(f"Successfully fetched {len(ohlc)} price points")
            return ohlc.reset_index()

        except requests.exceptions.RequestException as e:
            print(f"Request error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print("All retry attempts failed")
                return pd.DataFrame()

    return pd.DataFrame()