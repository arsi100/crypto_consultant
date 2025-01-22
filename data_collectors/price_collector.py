import requests
import pandas as pd
from datetime import datetime, timedelta
import logging
import random

logger = logging.getLogger(__name__)

def generate_mock_price_data(timeframe: str) -> pd.DataFrame:
    """Generate mock price data for testing"""
    now = datetime.now()

    # Set number of data points based on timeframe
    if timeframe == "24h":
        periods = 24
        freq = "H"
    elif timeframe == "7d":
        periods = 7 * 24
        freq = "H"
    else:  # 30d
        periods = 30
        freq = "D"

    # Generate timestamps
    timestamps = pd.date_range(end=now, periods=periods, freq=freq)

    # Generate mock prices with some randomness but following a pattern
    base_price = 45000  # Base price for BTC
    prices = []
    current_price = base_price

    for _ in range(periods):
        # Add some random movement (-2% to +2%)
        change = current_price * (random.uniform(-0.02, 0.02))
        current_price += change

        # Generate OHLC data
        open_price = current_price
        high_price = current_price * (1 + random.uniform(0, 0.01))
        low_price = current_price * (1 - random.uniform(0, 0.01))
        close_price = current_price * (1 + random.uniform(-0.005, 0.005))

        prices.append([open_price, high_price, low_price, close_price])

    # Create DataFrame
    df = pd.DataFrame(prices, columns=['open', 'high', 'low', 'close'])
    df['timestamp'] = timestamps

    return df

def get_crypto_prices(symbol: str, timeframe: str) -> pd.DataFrame:
    """
    Get cryptocurrency price data (currently using mock data)
    """
    try:
        logger.info(f"Generating mock price data for {symbol} with timeframe {timeframe}")
        price_data = generate_mock_price_data(timeframe)
        logger.info(f"Successfully generated {len(price_data)} price points")
        return price_data

    except Exception as e:
        logger.error(f"Error generating mock price data: {str(e)}")
        return pd.DataFrame()