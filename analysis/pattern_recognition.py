import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass

@dataclass
class PatternResult:
    pattern_type: str
    confidence: float
    start_idx: int
    end_idx: int
    description: str
    support_level: Optional[float] = None
    resistance_level: Optional[float] = None

def detect_head_and_shoulders(prices: pd.Series, window: int = 20) -> Optional[PatternResult]:
    """
    Detect head and shoulders pattern in price data
    Returns None if no pattern is found
    """
    try:
        if len(prices) < window:
            return None

        # Find local maxima
        peaks = []
        for i in range(1, len(prices)-1):
            if prices[i-1] < prices[i] > prices[i+1]:
                peaks.append((i, prices[i]))

        if len(peaks) < 3:
            return None

        # Look for head and shoulders pattern
        for i in range(len(peaks)-2):
            left = peaks[i]
            middle = peaks[i+1]
            right = peaks[i+2]

            # Check if middle peak is highest
            if middle[1] > left[1] and middle[1] > right[1]:
                # Check if shoulders are roughly equal height
                shoulder_diff = abs(left[1] - right[1])
                if shoulder_diff / left[1] < 0.1:  # 10% tolerance
                    # Calculate potential support level (neckline)
                    support = min(prices[left[0]:right[0]+1])
                    return PatternResult(
                        pattern_type="head_and_shoulders",
                        confidence=0.8,
                        start_idx=left[0],
                        end_idx=right[0],
                        description="Head and shoulders pattern detected - potential bearish reversal signal",
                        support_level=support,
                        resistance_level=middle[1]
                    )
    except Exception:
        return None
    return None

def detect_triangle_pattern(prices: pd.Series, window: int = 20) -> Optional[PatternResult]:
    """
    Detect ascending, descending, or symmetrical triangle patterns
    """
    try:
        if len(prices) < window:
            return None

        # Get highs and lows
        highs = pd.Series([max(prices[max(0, i-5):min(len(prices), i+6)]) 
                          for i in range(len(prices))])
        lows = pd.Series([min(prices[max(0, i-5):min(len(prices), i+6)]) 
                         for i in range(len(prices))])

        # Calculate trend lines using linear regression
        x = np.arange(len(highs))
        high_coeffs = np.polyfit(x, highs, 1)
        low_coeffs = np.polyfit(x, lows, 1)

        high_slope = high_coeffs[0]
        low_slope = low_coeffs[0]

        # Determine triangle type and convergence point
        if abs(high_slope) < 0.001 and low_slope > 0.001:
            pattern_type = "ascending_triangle"
            desc = "Ascending triangle pattern detected - potential bullish breakout"
            conf = 0.85
        elif high_slope < -0.001 and abs(low_slope) < 0.001:
            pattern_type = "descending_triangle"
            desc = "Descending triangle pattern detected - potential bearish breakout"
            conf = 0.85
        elif abs(high_slope + low_slope) < 0.002:
            pattern_type = "symmetrical_triangle"
            desc = "Symmetrical triangle pattern detected - watch for breakout direction"
            conf = 0.75
        else:
            return None

        # Calculate support and resistance levels
        support = low_coeffs[0] * len(prices) + low_coeffs[1]
        resistance = high_coeffs[0] * len(prices) + high_coeffs[1]

        return PatternResult(
            pattern_type=pattern_type,
            confidence=conf,
            start_idx=0,
            end_idx=len(prices)-1,
            description=desc,
            support_level=support,
            resistance_level=resistance
        )
    except Exception:
        return None
    return None

def calculate_bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2.0) -> Dict[str, float]:
    """
    Calculate Bollinger Bands with additional metrics
    """
    try:
        if len(prices) < window:
            return None

        rolling_mean = prices.rolling(window=window).mean()
        rolling_std = prices.rolling(window=window).std()

        upper_band = rolling_mean + (rolling_std * num_std)
        lower_band = rolling_mean - (rolling_std * num_std)

        # Calculate additional metrics
        bandwidth = (upper_band - lower_band) / rolling_mean * 100

        return {
            'middle': rolling_mean.iloc[-1],
            'upper': upper_band.iloc[-1],
            'lower': lower_band.iloc[-1],
            'bandwidth': bandwidth.iloc[-1],  # Bollinger Bandwidth
            'squeeze': bandwidth.iloc[-1] < bandwidth.rolling(window=20).mean().iloc[-1]  # Bollinger Squeeze indicator
        }
    except Exception:
        return None

def detect_divergence(prices: pd.Series, rsi: pd.Series, window: int = 20) -> Optional[PatternResult]:
    """
    Detect RSI divergence patterns
    """
    try:
        if len(prices) < window:
            return None

        # Find price and RSI peaks/troughs
        price_peaks = []
        rsi_peaks = []

        for i in range(1, len(prices)-1):
            if prices[i-1] < prices[i] > prices[i+1]:
                price_peaks.append((i, prices[i], 'peak'))
            elif prices[i-1] > prices[i] < prices[i+1]:
                price_peaks.append((i, prices[i], 'trough'))

            if rsi[i-1] < rsi[i] > rsi[i+1]:
                rsi_peaks.append((i, rsi[i], 'peak'))
            elif rsi[i-1] > rsi[i] < rsi[i+1]:
                rsi_peaks.append((i, rsi[i], 'trough'))

        # Look for divergence
        if len(price_peaks) >= 2 and len(rsi_peaks) >= 2:
            price_trend = price_peaks[-1][1] > price_peaks[-2][1]
            rsi_trend = rsi_peaks[-1][1] > rsi_peaks[-2][1]

            if price_trend != rsi_trend:
                pattern_type = "bullish_divergence" if not price_trend else "bearish_divergence"
                desc = (
                    "Bullish RSI divergence detected - potential reversal signal" 
                    if pattern_type == "bullish_divergence"
                    else "Bearish RSI divergence detected - potential reversal signal"
                )

                return PatternResult(
                    pattern_type=pattern_type,
                    confidence=0.75,
                    start_idx=min(price_peaks[-2][0], rsi_peaks[-2][0]),
                    end_idx=max(price_peaks[-1][0], rsi_peaks[-1][0]),
                    description=desc,
                    support_level=min(price_peaks[-2][1], price_peaks[-1][1]),
                    resistance_level=max(price_peaks[-2][1], price_peaks[-1][1])
                )
    except Exception:
        return None
    return None

def analyze_patterns(price_data: pd.DataFrame) -> Dict[str, Union[List[Dict], Dict, int]]:
    """
    Main function to analyze all patterns and indicators
    Returns a dictionary with pattern analysis results
    """
    try:
        close_prices = price_data['close']

        # Calculate RSI for divergence detection
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        patterns = []

        # Detect various patterns
        hs_pattern = detect_head_and_shoulders(close_prices)
        if hs_pattern:
            patterns.append(hs_pattern)

        triangle = detect_triangle_pattern(close_prices)
        if triangle:
            patterns.append(triangle)

        divergence = detect_divergence(close_prices, rsi)
        if divergence:
            patterns.append(divergence)

        # Calculate Bollinger Bands
        bb = calculate_bollinger_bands(close_prices)

        # Format patterns for output
        formatted_patterns = []
        for p in patterns:
            pattern_dict = {
                'type': p.pattern_type,
                'confidence': p.confidence,
                'description': p.description
            }
            if p.support_level is not None:
                pattern_dict['support'] = p.support_level
            if p.resistance_level is not None:
                pattern_dict['resistance'] = p.resistance_level
            formatted_patterns.append(pattern_dict)

        return {
            'patterns': formatted_patterns,
            'bollinger_bands': bb,
            'pattern_count': len(patterns),
            'rsi': rsi.iloc[-1] if not rsi.empty else None
        }

    except Exception as e:
        print(f"Error in pattern analysis: {str(e)}")
        return {'patterns': [], 'bollinger_bands': None, 'pattern_count': 0, 'rsi': None}