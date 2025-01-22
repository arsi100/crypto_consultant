import requests
import pandas as pd
from datetime import datetime, timedelta
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

class BinanceClient:
    BASE_URL = "https://api1.binance.com/api/v3"  # Using public API endpoint

    @staticmethod
    def get_symbol(crypto: str) -> str:
        """Convert crypto symbol to Binance pair format"""
        return f"{crypto.upper()}USDT"

    @staticmethod
    def get_interval(timeframe: str) -> tuple[str, int]:
        """Convert timeframe to Binance interval format and limit"""
        if timeframe == "24h":
            return "1h", 24
        elif timeframe == "7d":
            return "4h", 42
        else:  # 30d
            return "1d", 30

    @classmethod
    def get_klines(cls, symbol: str, interval: str, limit: int) -> Optional[list]:
        """Fetch kline/candlestick data from Binance with retry logic"""
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                url = f"{cls.BASE_URL}/klines"
                params = {
                    "symbol": symbol,
                    "interval": interval,
                    "limit": limit
                }

                response = requests.get(
                    url, 
                    params=params, 
                    timeout=10,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )

                if response.status_code == 451:
                    logger.error("Regional restriction detected, falling back to mock data")
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
        freq = "H"
    elif timeframe == "7d":
        periods = 7 * 24
        freq = "H"
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
    """Get cryptocurrency price data with fallback to mock data"""
    try:
        symbol = BinanceClient.get_symbol(crypto)
        interval, limit = BinanceClient.get_interval(timeframe)

        logger.info(f"Fetching {timeframe} price data for {symbol} from Binance")
        klines = BinanceClient.get_klines(symbol, interval, limit)

        if klines:
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
                'taker_buy_quote_volume', 'ignore'
            ])

            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            price_columns = ['open', 'high', 'low', 'close']
            df[price_columns] = df[price_columns].astype(float)

            result = df[['timestamp', 'open', 'high', 'low', 'close']]
            logger.info(f"Successfully fetched {len(result)} price points from Binance")
            return result

        logger.warning("Falling back to mock data generation")
        mock_data = generate_mock_price_data(timeframe)
        logger.info(f"Generated {len(mock_data)} mock price points")
        return mock_data

    except Exception as e:
        logger.error(f"Error in get_crypto_prices: {str(e)}")
        logger.warning("Falling back to mock data due to error")
        return generate_mock_price_data(timeframe)