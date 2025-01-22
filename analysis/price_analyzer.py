import pandas as pd
import numpy as np
from typing import Dict

def analyze_price_trends(price_data: pd.DataFrame) -> Dict:
    """
    Analyze price trends using technical indicators and provide detailed analysis
    """
    if price_data.empty:
        return {
            'trend': 'unknown',
            'indicators': {},
            'support_resistance': {},
            'analysis': 'No price data available for analysis'
        }

    # Calculate basic technical indicators
    close_prices = price_data['close']

    # Simple Moving Averages
    sma_20 = close_prices.rolling(window=20).mean()
    sma_50 = close_prices.rolling(window=50).mean()

    # Relative Strength Index (RSI)
    delta = close_prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # MACD
    exp1 = close_prices.ewm(span=12, adjust=False).mean()
    exp2 = close_prices.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()

    # Get current values
    current_price = close_prices.iloc[-1]
    current_sma_20 = sma_20.iloc[-1]
    current_sma_50 = sma_50.iloc[-1]
    current_rsi = rsi.iloc[-1]
    current_macd = macd.iloc[-1]
    current_signal = signal.iloc[-1]

    # Determine trend and momentum
    trend_strength = 'strong' if abs(current_price - current_sma_20) / current_sma_20 > 0.02 else 'moderate'
    trend = 'bullish' if current_price > current_sma_20 > current_sma_50 else 'bearish' if current_price < current_sma_20 < current_sma_50 else 'sideways'

    # Generate analysis text
    price_change = ((current_price - close_prices.iloc[-2]) / close_prices.iloc[-2]) * 100
    analysis = f"Price is showing a {trend_strength} {trend} trend with {abs(price_change):.2f}% {'increase' if price_change > 0 else 'decrease'} "

    if current_rsi > 70:
        analysis += "and is currently overbought (RSI > 70). Consider potential price correction. "
    elif current_rsi < 30:
        analysis += "and is currently oversold (RSI < 30). Watch for potential reversal. "
    else:
        analysis += f"with neutral RSI at {current_rsi:.1f}. "

    if current_macd > current_signal:
        analysis += "MACD indicates bullish momentum building up."
    else:
        analysis += "MACD suggests momentum may be weakening."

    # Calculate support and resistance levels using recent price action
    window = min(len(price_data), 20)  # Use last 20 periods or all available data
    recent_prices = price_data.tail(window)
    support = recent_prices['low'].nlargest(3).mean()  # Average of 3 highest lows
    resistance = recent_prices['high'].nsmallest(3).mean()  # Average of 3 lowest highs

    return {
        'trend': trend,
        'trend_strength': trend_strength,
        'indicators': {
            'sma_20': round(current_sma_20, 2),
            'sma_50': round(current_sma_50, 2),
            'rsi': round(current_rsi, 2),
            'macd': round(current_macd, 4),
            'macd_signal': round(current_signal, 4)
        },
        'support_resistance': {
            'support': round(support, 2),
            'resistance': round(resistance, 2)
        },
        'analysis': analysis,
        'price_change_percent': round(price_change, 2)
    }