import requests
import pandas as pd
from datetime import datetime, timedelta
import logging
import time
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

        for attempt in range(max_retries):
            try:
                url = f"{cls.BASE_URL}/coins/{coin_id}/market_chart"
                params = {
                    "vs_currency": vs_currency,
                    "days": days,
                    "interval": "hourly" if days == "1" else "daily"
                }

                response = requests.get(
                    url, 
                    params=params, 
                    timeout=10,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )

                if response.status_code == 429:
                    logger.error("Rate limit exceeded, falling back to mock data")
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

    return df[['timestamp', 'open', 'high', 'low', 'close']]

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
            # For simplicity, we'll use the same close price for open, high, and low
            # as CoinGecko's free API doesn't provide OHLC data
            prices_df['open'] = prices_df['close']
            prices_df['high'] = prices_df['close']
            prices_df['low'] = prices_df['close']

            result = prices_df[['timestamp', 'open', 'high', 'low', 'close']]
            logger.info(f"Successfully fetched {len(result)} price points from CoinGecko")
            return result

        logger.warning("Falling back to mock data generation")
        mock_data = generate_mock_price_data(timeframe)
        logger.info(f"Generated {len(mock_data)} mock price points")
        return mock_data

    except Exception as e:
        logger.error(f"Error in get_crypto_prices: {str(e)}")
        logger.warning("Falling back to mock data due to error")
        return generate_mock_price_data(timeframe)