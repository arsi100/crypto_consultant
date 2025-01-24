import os
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from openai import OpenAI

logger = logging.getLogger(__name__)

class AIAnalyzer:
    def __init__(self):
        self.client = OpenAI()

    def _format_number(self, value: Optional[float], format_str: str = ",.2f") -> str:
        """Safely format numbers with null checking"""
        if value is None or pd.isna(value):
            return "N/A"
        try:
            return f"{value:{format_str}}"
        except (ValueError, TypeError):
            return str(value)

    def analyze_price_data(self, price_data: pd.DataFrame, timeframe: str) -> Dict[str, Any]:
        """Analyze price data using OpenAI to generate insights"""
        try:
            # Calculate basic metrics
            latest_price = price_data['close'].iloc[-1] if not price_data.empty else None
            first_price = price_data['close'].iloc[0] if not price_data.empty else None
            price_change = ((latest_price - first_price) / first_price * 100) if all(x is not None for x in [latest_price, first_price]) else 0
            high = price_data['high'].max() if not price_data.empty else None
            low = price_data['low'].min() if not price_data.empty else None
            volume = price_data['volume'].sum() if 'volume' in price_data.columns and not price_data.empty else None

            # Calculate technical indicators for context
            rolling_window = min(20, len(price_data))
            sma = price_data['close'].rolling(window=rolling_window).mean().iloc[-1] if not price_data.empty else None
            rsi = 50  # Placeholder - implement actual RSI calculation if needed

            # Prepare data summary for AI analysis
            data_summary = (
                f"Analyze the following {timeframe} cryptocurrency market data:\n\n"
                f"Current Price: ${self._format_number(latest_price)}\n"
                f"24h Change: {self._format_number(price_change)}%\n"
                f"24h High: ${self._format_number(high)}\n"
                f"24h Low: ${self._format_number(low)}\n"
                f"24h Volume: {self._format_number(volume, ',.0f')}\n"
                f"SMA{rolling_window}: ${self._format_number(sma)}\n"
                f"RSI: {self._format_number(rsi)}\n"
                f"Number of data points: {len(price_data)}\n\n"
                f"Provide a detailed cryptocurrency market analysis focusing on:\n"
                f"1. Current market structure and trend\n"
                f"2. Key support/resistance levels\n"
                f"3. Volume analysis and market participation\n"
                f"4. Short-term price targets\n"
                f"5. Risk assessment"
            )

            # Get AI analysis
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a professional cryptocurrency market analyst specializing in technical analysis and market psychology. 
                        Analyze the provided market data and generate actionable insights.

                        FORMAT YOUR RESPONSE AS A VALID JSON STRING LIKE THIS (no additional text):
                        {
                            "trend": "bullish/bearish/neutral",
                            "trend_strength": "strong/moderate/weak",
                            "analysis": "Start with clear market context. Include specific price levels and technical analysis. Explain the reasoning behind support/resistance levels. Discuss volume profile and market participation. Provide actionable insights.",
                            "patterns": [
                                {
                                    "type": "pattern name (e.g. Double Bottom, Bull Flag)",
                                    "confidence": 0.95,
                                    "price_target": 45000
                                }
                            ],
                            "support_resistance": {
                                "support": [42000, 41000],
                                "resistance": [45000, 46000]
                            },
                            "signal": "BUY/SELL/HOLD",
                            "confidence": 0.85,
                            "market_sentiment": "bullish/bearish/neutral",
                            "risk_level": "high/medium/low"
                        }"""
                    },
                    {"role": "user", "content": data_summary}
                ]
            )

            # Parse and validate AI analysis
            analysis = response.choices[0].message.content
            try:
                import json
                if isinstance(analysis, str):
                    analysis = json.loads(analysis)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                analysis = {}

            return {
                **analysis,
                "price_change_percent": float(price_change) if price_change is not None else 0.0,
                "latest_price": float(latest_price) if latest_price is not None else 0.0
            }

        except Exception as e:
            logger.error(f"Error in AI price analysis: {str(e)}")
            return {
                "trend": "unknown",
                "trend_strength": "unknown",
                "analysis": f"Error analyzing price data: {str(e)}",
                "patterns": [],
                "support_resistance": {"support": None, "resistance": None},
                "signal": "HOLD",
                "confidence": 0,
                "market_sentiment": "neutral",
                "price_change_percent": 0,
                "latest_price": 0
            }

    def analyze_patterns(self, price_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify and analyze price patterns using AI"""
        try:
            if price_data.empty:
                return []

            price_data['returns'] = price_data['close'].pct_change()
            volatility = price_data['returns'].std()

            # Prepare pattern analysis prompt
            data_description = (
                f"Analyze the following cryptocurrency price action:\n\n"
                f"Price Volatility: {self._format_number(volatility)}\n"
                f"Price Movement: {self._format_number(price_data['close'].iloc[-1] - price_data['close'].iloc[0])}\n"
                f"Candles Analyzed: {len(price_data)}\n\n"
                f"Identify any significant chart patterns, focusing on:\n"
                f"1. Traditional patterns (Head & Shoulders, Double Top/Bottom)\n"
                f"2. Candlestick patterns (Engulfing, Doji, etc.)\n"
                f"3. Continuation and reversal patterns\n"
                f"4. Volume confirmation\n"
                f"5. Pattern completion percentage"
            )

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a cryptocurrency pattern recognition expert.
                        Analyze the price action and identify significant chart patterns.

                        FORMAT YOUR RESPONSE AS A VALID JSON STRING LIKE THIS (no additional text):
                        {
                            "patterns": [
                                {
                                    "type": "pattern name",
                                    "confidence": 0.95,
                                    "description": "Detailed pattern description with price targets and confirmation levels",
                                    "completion": 0.80,
                                    "volume_confirmed": true
                                }
                            ]
                        }"""
                    },
                    {"role": "user", "content": data_description}
                ]
            )

            # Parse and validate response
            analysis = response.choices[0].message.content
            try:
                if isinstance(analysis, str):
                    analysis = json.loads(analysis)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse pattern analysis response as JSON: {e}")
                return []

            return analysis.get("patterns", [])

        except Exception as e:
            logger.error(f"Error in pattern analysis: {str(e)}")
            return []