import requests
import pandas as pd
from datetime import datetime, timedelta
import logging
import time
import os
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
        api_key = os.environ.get('COINGECKO_API_KEY')

        for attempt in range(max_retries):
            try:
                url = f"{cls.BASE_URL}/coins/{coin_id}/market_chart"
                params = {
                    "vs_currency": vs_currency,
                    "days": days,
                    "interval": "hourly" if days == "1" else "daily",
                    "x_cg_demo_api_key": api_key
                }

                headers = {
                    'X-Cg-Api-Key': api_key,
                    'User-Agent': 'CryptoIntelligence/1.0'
                }

                response = requests.get(
                    url, 
                    params=params, 
                    headers=headers,
                    timeout=10
                )

                if response.status_code == 429:
                    logger.error("Rate limit exceeded")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
                        continue
                    return None

                if response.status_code == 401:
                    logger.error("Unauthorized - Invalid API key")
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
            prices_df = pd.DataFrame(market_data['prices'], columns=['timestamp', 'close'])
            prices_df['timestamp'] = pd.to_datetime(prices_df['timestamp'], unit='ms')

            # Calculate OHLC from price data
            ohlc = prices_df.set_index('timestamp')['close'].resample('1H' if timeframe == "24h" else '1D').ohlc()
            result = ohlc.reset_index()

            logger.info(f"Successfully fetched {len(result)} price points from CoinGecko")
            return result

        logger.warning("Falling back to mock data generation")
        return generate_mock_price_data(timeframe)

    except Exception as e:
        logger.error(f"Error in get_crypto_prices: {str(e)}")
        return generate_mock_price_data(timeframe)

def generate_mock_price_data(timeframe: str) -> pd.DataFrame:
    """Generate mock price data as fallback"""
    now = datetime.now()

    if timeframe == "24h":
        periods = 24
        freq = "h"
    elif timeframe == "7d":
        periods = 7 * 24
        freq = "h"
    else:  # 30d
        periods = 30
        freq = "D"

    timestamps = pd.date_range(end=now, periods=periods, freq=freq)
    base_price = 45000  # Base BTC price
    volatility = 0.02   # 2% price movement

    prices = []
    current_price = base_price

    for _ in range(periods):
        change = current_price * (2 * volatility * (0.5 - time.time() % 1))
        current_price += change

        open_price = current_price
        high_price = current_price * (1 + volatility/2)
        low_price = current_price * (1 - volatility/2)
        close_price = current_price * (1 + (time.time() % 1 - 0.5) * volatility)

        prices.append([open_price, high_price, low_price, close_price])

    df = pd.DataFrame(prices, columns=['open', 'high', 'low', 'close'])
    df['timestamp'] = timestamps

    logger.info(f"Generated {len(df)} mock price points")
    return df[['timestamp', 'open', 'high', 'low', 'close']]