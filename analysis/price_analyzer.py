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
        'price_change_percent': 0.0,
        'market_sentiment': 'Neutral',
        'signal': 'HOLD',
        'confidence': 0.0
    }

    try:
        # Calculate basic technical indicators
        close_prices = price_data['close']

        # Simple Moving Averages
        sma_20 = close_prices.rolling(window=20).mean()
        sma_50 = close_prices.rolling(window=50).mean()

        # RSI
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

        # Current values
        current_price = close_prices.iloc[-1]
        current_sma_20 = sma_20.iloc[-1]
        current_sma_50 = sma_50.iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]

        # Pattern Recognition
        pattern_analysis = analyze_patterns(price_data)

        # Determine trend and momentum
        price_change = ((current_price - close_prices.iloc[-2]) / close_prices.iloc[-2]) * 100

        # Trend analysis
        trend = 'unknown'
        trend_strength = 'unknown'
        confidence = 0.0
        signal = 'HOLD'

        if not pd.isna(current_sma_20) and not pd.isna(current_sma_50):
            price_deviation = abs(current_price - current_sma_20) / current_sma_20
            trend_strength = 'strong' if price_deviation > 0.02 else 'moderate'

            if current_price > current_sma_20 > current_sma_50:
                trend = 'bullish'
                confidence = min(price_deviation * 5, 0.95)
                signal = 'BUY' if price_deviation > 0.03 else 'HOLD'
            elif current_price < current_sma_20 < current_sma_50:
                trend = 'bearish'
                confidence = min(price_deviation * 5, 0.95)
                signal = 'SELL' if price_deviation > 0.03 else 'HOLD'
            else:
                trend = 'sideways'
                confidence = 0.5
                signal = 'HOLD'

        # Generate analysis text
        analysis = f"The market is showing a {trend_strength} {trend} trend"

        if price_change != 0:
            analysis += f" with {abs(price_change):.2f}% {'increase' if price_change > 0 else 'decrease'}"

        if not pd.isna(current_rsi):
            if current_rsi > 70:
                analysis += ". Market is currently overbought (RSI > 70)"
                if trend == 'bullish':
                    analysis += ". Consider taking profits"
            elif current_rsi < 30:
                analysis += ". Market is currently oversold (RSI < 30)"
                if trend == 'bearish':
                    analysis += ". Watch for potential reversal"

        if not pd.isna(current_macd) and not pd.isna(current_signal):
            if current_macd > current_signal:
                analysis += ". MACD indicates bullish momentum"
            else:
                analysis += ". MACD suggests bearish pressure"

        # Add pattern analysis
        if pattern_analysis['patterns']:
            analysis += "\nDetected patterns:"
            for pattern in pattern_analysis['patterns'][:2]:
                analysis += f"\n• {pattern['description']}"

        result = {
            'trend': trend,
            'trend_strength': trend_strength,
            'signal': signal,
            'confidence': confidence,
            'indicators': {
                'sma_20': float(current_sma_20) if not pd.isna(current_sma_20) else None,
                'sma_50': float(current_sma_50) if not pd.isna(current_sma_50) else None,
                'rsi': float(current_rsi) if not pd.isna(current_rsi) else None,
                'macd': float(current_macd) if not pd.isna(current_macd) else None,
                'macd_signal': float(current_signal) if not pd.isna(current_signal) else None
            },
            'patterns': pattern_analysis['patterns'],
            'bollinger_bands': pattern_analysis['bollinger_bands'],
            'support_resistance': {
                'support': float(pattern_analysis['bollinger_bands']['lower']) if pattern_analysis['bollinger_bands'] else None,
                'resistance': float(pattern_analysis['bollinger_bands']['upper']) if pattern_analysis['bollinger_bands'] else None
            },
            'analysis': analysis,
            'price_change_percent': float(price_change),
            'market_sentiment': 'Bullish' if trend == 'bullish' else 'Bearish' if trend == 'bearish' else 'Neutral'
        }

        return result

    except Exception as e:
        print(f"Error in price analysis: {str(e)}")
        return default_response