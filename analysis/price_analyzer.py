import pandas as pd
import numpy as np
from typing import Dict
import time
from analysis.pattern_recognition import analyze_patterns
from analysis.ai_analyzer import AIAnalyzer

def analyze_price_trends(price_data: pd.DataFrame, timeframe: str = '24h') -> Dict:
    """
    Analyze price trends using both AI and technical indicators
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
        # Initialize AI analyzer
        ai_analyzer = AIAnalyzer()

        # Get AI analysis
        ai_analysis = ai_analyzer.analyze_price_data(price_data, timeframe)

        # Calculate technical indicators as backup and supplementary data
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

        # Get pattern analysis
        pattern_analysis = analyze_patterns(price_data)

        # Combine AI and traditional analysis
        result = {
            'trend': ai_analysis.get('trend', 'unknown'),
            'trend_strength': ai_analysis.get('trend_strength', 'unknown'),
            'signal': ai_analysis.get('signal', 'HOLD'),
            'confidence': ai_analysis.get('confidence', 0.0),
            'indicators': {
                'sma_20': float(current_sma_20) if not pd.isna(current_sma_20) else None,
                'sma_50': float(current_sma_50) if not pd.isna(current_sma_50) else None,
                'rsi': float(current_rsi) if not pd.isna(current_rsi) else None,
                'macd': float(current_macd) if not pd.isna(current_macd) else None,
                'macd_signal': float(current_signal) if not pd.isna(current_signal) else None
            },
            'patterns': pattern_analysis['patterns'],
            'bollinger_bands': pattern_analysis['bollinger_bands'],
            'support_resistance': ai_analysis.get('support_resistance', {
                'support': pattern_analysis['bollinger_bands']['lower'] if pattern_analysis['bollinger_bands'] else None,
                'resistance': pattern_analysis['bollinger_bands']['upper'] if pattern_analysis['bollinger_bands'] else None
            }),
            'analysis': ai_analysis.get('analysis', 'Analysis not available'),
            'price_change_percent': float(ai_analysis.get('price_change_percent', 0.0)),
            'market_sentiment': ai_analysis.get('market_sentiment', 'Neutral')
        }

        return result

    except Exception as e:
        print(f"Error in price analysis: {str(e)}")
        return default_response