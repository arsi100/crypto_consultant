import pandas as pd
import numpy as np
from typing import Dict
import time
from analysis.pattern_recognition import analyze_patterns

def analyze_price_trends(price_data: pd.DataFrame) -> Dict:
    """
    Analyze price trends using technical indicators and provide detailed analysis
    """
    default_response = {
        'trend': 'unknown',
        'trend_strength': 'unknown',
        'indicators': {
            'sma_20': None,
            'sma_50': None,
            'rsi': None,
            'macd': None,
            'macd_signal': None
        },
        'support_resistance': {
            'support': None,
            'resistance': None
        },
        'patterns': [],
        'bollinger_bands': None,
        'analysis': 'No price data available for analysis',
        'price_change_percent': 0.0
    }

    # Validate input data
    if price_data is None or not isinstance(price_data, pd.DataFrame):
        print("Invalid price data format")
        return default_response

    if price_data.empty or len(price_data) < 2:  # Need at least 2 points for analysis
        print("Insufficient price data points")
        return default_response

    try:
        # Calculate basic technical indicators
        close_prices = price_data['close']

        # Ensure we have numeric data
        if not pd.to_numeric(close_prices, errors='coerce').notna().all():
            print("Non-numeric values found in close prices")
            return default_response

        # Simple Moving Averages
        sma_20 = close_prices.rolling(window=min(20, len(close_prices))).mean()
        sma_50 = close_prices.rolling(window=min(50, len(close_prices))).mean()

        # Relative Strength Index (RSI)
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=min(14, len(close_prices))).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=min(14, len(close_prices))).mean()
        rs = gain / loss.replace(0, np.inf)  # Handle division by zero
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

        # Pattern Recognition
        pattern_analysis = analyze_patterns(price_data)

        # Determine trend and momentum
        try:
            price_change = ((current_price - close_prices.iloc[-2]) / close_prices.iloc[-2]) * 100
        except (IndexError, ZeroDivisionError):
            print("Error calculating price change")
            price_change = 0

        # Default to unknown if moving averages are not available
        trend = 'unknown'
        trend_strength = 'unknown'

        if not pd.isna(current_sma_20) and not pd.isna(current_sma_50):
            trend_strength = 'strong' if abs(current_price - current_sma_20) / current_sma_20 > 0.02 else 'moderate'
            if current_price > current_sma_20 > current_sma_50:
                trend = 'bullish'
            elif current_price < current_sma_20 < current_sma_50:
                trend = 'bearish'
            else:
                trend = 'sideways'

        # Generate analysis text
        analysis = f"Price is showing a {trend_strength} {trend} trend"
        if price_change != 0:
            analysis += f" with {abs(price_change):.2f}% {'increase' if price_change > 0 else 'decrease'}"

        if not pd.isna(current_rsi):
            if current_rsi > 70:
                analysis += ". Market is currently overbought (RSI > 70). Consider potential price correction"
            elif current_rsi < 30:
                analysis += ". Market is currently oversold (RSI < 30). Watch for potential reversal"
            else:
                analysis += f". RSI is neutral at {current_rsi:.1f}"

        if not pd.isna(current_macd) and not pd.isna(current_signal):
            if current_macd > current_signal:
                analysis += ". MACD indicates bullish momentum building up"
            else:
                analysis += ". MACD suggests momentum may be weakening"

        # Add pattern analysis to the report
        if pattern_analysis['patterns']:
            analysis += "\n\nDetected patterns:"
            for pattern in pattern_analysis['patterns']:
                analysis += f"\n• {pattern['description']} (Confidence: {pattern['confidence']:.0%})"

        # Add Bollinger Bands analysis
        if pattern_analysis['bollinger_bands']:
            bb = pattern_analysis['bollinger_bands']
            current_bb_position = (current_price - bb['lower']) / (bb['upper'] - bb['lower'])

            if current_bb_position > 0.95:
                analysis += "\n• Price is near upper Bollinger Band - potential resistance"
            elif current_bb_position < 0.05:
                analysis += "\n• Price is near lower Bollinger Band - potential support"

        result = {
            'trend': trend,
            'trend_strength': trend_strength,
            'indicators': {
                'sma_20': round(float(current_sma_20), 2) if not pd.isna(current_sma_20) else None,
                'sma_50': round(float(current_sma_50), 2) if not pd.isna(current_sma_50) else None,
                'rsi': round(float(current_rsi), 2) if not pd.isna(current_rsi) else None,
                'macd': round(float(current_macd), 4) if not pd.isna(current_macd) else None,
                'macd_signal': round(float(current_signal), 4) if not pd.isna(current_signal) else None
            },
            'patterns': pattern_analysis['patterns'],
            'bollinger_bands': pattern_analysis['bollinger_bands'],
            'support_resistance': {
                'support': round(pattern_analysis['bollinger_bands']['lower'], 2) if pattern_analysis['bollinger_bands'] else None,
                'resistance': round(pattern_analysis['bollinger_bands']['upper'], 2) if pattern_analysis['bollinger_bands'] else None
            },
            'analysis': analysis,
            'price_change_percent': round(price_change, 2)
        }

        return result

    except Exception as e:
        print(f"Error in price analysis: {str(e)}")
        return default_response