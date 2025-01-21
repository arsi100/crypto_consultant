import pandas as pd
import numpy as np
from typing import Dict

def analyze_price_trends(price_data: pd.DataFrame) -> Dict:
    """
    Analyze price trends using technical indicators
    """
    if price_data.empty:
        return {
            'trend': 'unknown',
            'indicators': {},
            'support_resistance': {}
        }

    # Calculate basic technical indicators
    close_prices = price_data['close']
    
    # Simple Moving Averages
    sma_20 = close_prices.rolling(window=20).mean().iloc[-1]
    sma_50 = close_prices.rolling(window=50).mean().iloc[-1]

    # Relative Strength Index (RSI)
    delta = close_prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs)).iloc[-1]

    # Determine trend
    current_price = close_prices.iloc[-1]
    trend = 'bullish' if current_price > sma_20 > sma_50 else 'bearish'

    # Calculate support and resistance levels
    price_range = price_data['high'].max() - price_data['low'].min()
    support = price_data['low'].rolling(window=20).min().iloc[-1]
    resistance = price_data['high'].rolling(window=20).max().iloc[-1]

    return {
        'trend': trend,
        'indicators': {
            'sma_20': round(sma_20, 2),
            'sma_50': round(sma_50, 2),
            'rsi': round(rsi, 2)
        },
        'support_resistance': {
            'support': round(support, 2),
            'resistance': round(resistance, 2)
        }
    }
