import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class PatternResult:
    pattern_type: str
    confidence: float
    start_idx: int
    end_idx: int
    description: str

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
                    return PatternResult(
                        pattern_type="head_and_shoulders",
                        confidence=0.8,
                        start_idx=left[0],
                        end_idx=right[0],
                        description="Head and shoulders pattern detected - potential reversal signal"
                    )
    except Exception:
        return None
    return None

def detect_double_top_bottom(prices: pd.Series, window: int = 20) -> Optional[PatternResult]:
    """
    Detect double top or double bottom patterns
    """
    try:
        if len(prices) < window:
            return None
            
        # Find local extrema
        tops = []
        bottoms = []
        for i in range(1, len(prices)-1):
            if prices[i-1] < prices[i] > prices[i+1]:
                tops.append((i, prices[i]))
            if prices[i-1] > prices[i] < prices[i+1]:
                bottoms.append((i, prices[i]))
                
        # Check for double top
        if len(tops) >= 2:
            for i in range(len(tops)-1):
                price_diff = abs(tops[i][1] - tops[i+1][1])
                if price_diff / tops[i][1] < 0.02:  # 2% tolerance
                    return PatternResult(
                        pattern_type="double_top",
                        confidence=0.85,
                        start_idx=tops[i][0],
                        end_idx=tops[i+1][0],
                        description="Double top pattern detected - potential bearish reversal"
                    )
                    
        # Check for double bottom
        if len(bottoms) >= 2:
            for i in range(len(bottoms)-1):
                price_diff = abs(bottoms[i][1] - bottoms[i+1][1])
                if price_diff / bottoms[i][1] < 0.02:  # 2% tolerance
                    return PatternResult(
                        pattern_type="double_bottom",
                        confidence=0.85,
                        start_idx=bottoms[i][0],
                        end_idx=bottoms[i+1][0],
                        description="Double bottom pattern detected - potential bullish reversal"
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
                         
        # Calculate trend lines
        high_slope = np.polyfit(range(len(highs)), highs, 1)[0]
        low_slope = np.polyfit(range(len(lows)), lows, 1)[0]
        
        # Determine triangle type
        if abs(high_slope) < 0.001 and low_slope > 0.001:
            pattern_type = "ascending_triangle"
            desc = "Ascending triangle pattern - potential bullish breakout"
        elif high_slope < -0.001 and abs(low_slope) < 0.001:
            pattern_type = "descending_triangle"
            desc = "Descending triangle pattern - potential bearish breakout"
        elif abs(high_slope + low_slope) < 0.001:
            pattern_type = "symmetrical_triangle"
            desc = "Symmetrical triangle pattern - watch for breakout"
        else:
            return None
            
        return PatternResult(
            pattern_type=pattern_type,
            confidence=0.75,
            start_idx=0,
            end_idx=len(prices)-1,
            description=desc
        )
    except Exception:
        return None
    return None

def calculate_bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2.0) -> Dict:
    """
    Calculate Bollinger Bands
    """
    try:
        if len(prices) < window:
            return None
            
        rolling_mean = prices.rolling(window=window).mean()
        rolling_std = prices.rolling(window=window).std()
        
        upper_band = rolling_mean + (rolling_std * num_std)
        lower_band = rolling_mean - (rolling_std * num_std)
        
        return {
            'middle': rolling_mean.iloc[-1],
            'upper': upper_band.iloc[-1],
            'lower': lower_band.iloc[-1],
            'width': (upper_band.iloc[-1] - lower_band.iloc[-1]) / rolling_mean.iloc[-1]
        }
    except Exception:
        return None

def analyze_patterns(price_data: pd.DataFrame) -> Dict:
    """
    Main function to analyze all patterns and indicators
    """
    try:
        close_prices = price_data['close']
        
        patterns = []
        
        # Detect chart patterns
        hs_pattern = detect_head_and_shoulders(close_prices)
        if hs_pattern:
            patterns.append(hs_pattern)
            
        dtb_pattern = detect_double_top_bottom(close_prices)
        if dtb_pattern:
            patterns.append(dtb_pattern)
            
        triangle = detect_triangle_pattern(close_prices)
        if triangle:
            patterns.append(triangle)
            
        # Calculate Bollinger Bands
        bb = calculate_bollinger_bands(close_prices)
        
        return {
            'patterns': [
                {
                    'type': p.pattern_type,
                    'confidence': p.confidence,
                    'description': p.description
                } for p in patterns
            ],
            'bollinger_bands': bb,
            'pattern_count': len(patterns)
        }
        
    except Exception as e:
        print(f"Error in pattern analysis: {str(e)}")
        return {'patterns': [], 'bollinger_bands': None, 'pattern_count': 0}
