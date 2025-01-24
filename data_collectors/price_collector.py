import requests
import pandas as pd
from datetime import datetime, timedelta
import logging
import time
import os
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)

class CoinGeckoClient:
    BASE_URL = "https://api.coingecko.com/api/v3"

    @staticmethod
    def get_coin_id(crypto: str) -> str:
        """Convert crypto symbol to CoinGecko coin id"""
        mapping = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'USDT': 'tether',
            'BNB': 'binancecoin',
            'SOL': 'solana'
        }
        return mapping.get(crypto.upper(), 'bitcoin')

    @classmethod
    def get_market_chart(cls, coin_id: str, vs_currency: str, days: str) -> Optional[dict]:
        """Fetch market chart data from CoinGecko with retry logic"""
        max_retries = 3
        retry_delay = 1
        api_key = os.environ.get('COINGECKO_API_KEY', '').strip()

        if not api_key:
            logger.error("CoinGecko API key not found")
            return None

        for attempt in range(max_retries):
            try:
                url = f"{cls.BASE_URL}/coins/{coin_id}/market_chart"
                params = {
                    "vs_currency": vs_currency,
                    "days": days,
                    "interval": "hourly" if days == "1" else "daily"
                }

                headers = {
                    'x-cg-api-key': api_key  # Changed from 'X-Cg-Api-Key' to lowercase
                }

                response = requests.get(
                    url, 
                    params=params, 
                    headers=headers,
                    timeout=10
                )

                if response.status_code == 429:
                    logger.warning(f"Rate limit exceeded (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
                        continue
                    return None

                if response.status_code == 401:
                    logger.error(f"Unauthorized - Invalid API key: {api_key[:5]}...")
                    return None

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    logger.error("All retry attempts failed")
                    return None

        return None

def get_crypto_prices(crypto: str, timeframe: str) -> pd.DataFrame:
    """Get cryptocurrency price data from CoinGecko with fallback to mock data"""
    try:
        coin_id = CoinGeckoClient.get_coin_id(crypto)

        # Convert timeframe to days parameter
        days_map = {"24h": "1", "7d": "7", "30d": "30"}
        days = days_map.get(timeframe, "1")

        logger.info(f"Fetching {timeframe} price data for {coin_id} from CoinGecko")
        market_data = CoinGeckoClient.get_market_chart(coin_id, "usd", days)

        if market_data and 'prices' in market_data:
            # Convert price data to DataFrame
            prices_df = pd.DataFrame(market_data['prices'], columns=['timestamp', 'price'])
            prices_df['timestamp'] = pd.to_datetime(prices_df['timestamp'], unit='ms')

            # Calculate OHLC
            ohlc = prices_df.set_index('timestamp')['price'].resample('1h' if timeframe == "24h" else '1D').ohlc()
            result = ohlc.reset_index()

            logger.info(f"Successfully fetched {len(result)} price points from CoinGecko")
            return result

        logger.warning("Falling back to mock data generation")
        return generate_mock_price_data(timeframe, crypto)

    except Exception as e:
        logger.error(f"Error in get_crypto_prices: {str(e)}")
        return generate_mock_price_data(timeframe, crypto)

def generate_mock_price_data(timeframe: str, crypto: str) -> pd.DataFrame:
    """Generate realistic mock price data as fallback based on current market prices"""
    now = datetime.now()

    # More realistic base prices for different cryptocurrencies
    base_prices = {
        'BTC': 106000,  # Updated to current approximate price
        'ETH': 3200,
        'USDT': 1,
        'BNB': 300,
        'SOL': 100
    }

    base_price = base_prices.get(crypto.upper(), 100)  # Default to 100 if unknown

    if timeframe == "24h":
        periods = 24
        freq = "h"
        volatility = 0.02
    elif timeframe == "7d":
        periods = 7 * 24
        freq = "h"
        volatility = 0.03
    else:  # 30d
        periods = 30
        freq = "D"
        volatility = 0.05

    timestamps = pd.date_range(end=now, periods=periods, freq=freq)

    # Generate more realistic price movements using random walk
    returns = np.random.normal(loc=0, scale=volatility, size=periods)
    prices = base_price * np.exp(np.cumsum(returns))

    # Generate OHLC data
    data = []
    for i in range(len(timestamps)):
        current_price = prices[i]
        high_low_spread = current_price * volatility

        open_price = current_price * (1 + np.random.uniform(-volatility/2, volatility/2))
        high_price = max(open_price, current_price) + abs(np.random.normal(0, high_low_spread/2))
        low_price = min(open_price, current_price) - abs(np.random.normal(0, high_low_spread/2))
        close_price = current_price

        data.append([timestamps[i], open_price, high_price, low_price, close_price])

    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
    logger.info(f"Generated {len(df)} mock price points for {crypto}")
    return df