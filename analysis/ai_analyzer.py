import os
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from openai import OpenAI

logger = logging.getLogger(__name__)

class AIAnalyzer:
    def __init__(self):
        self.client = OpenAI()

    def analyze_price_data(self, price_data: pd.DataFrame, timeframe: str) -> Dict[str, Any]:
        """Analyze price data using OpenAI to generate insights"""
        try:
            # Calculate basic metrics
            latest_price = price_data['close'].iloc[-1]
            price_change = (latest_price - price_data['close'].iloc[0]) / price_data['close'].iloc[0] * 100
            high = price_data['high'].max()
            low = price_data['low'].min()
            volume = price_data['volume'].sum() if 'volume' in price_data else None

            # Prepare data summary for AI analysis
            data_summary = (
                f"Timeframe: {timeframe}\n"
                f"Latest Price: ${latest_price:,.2f}\n"
                f"Price Change: {price_change:.2f}%\n"
                f"High: ${high:,.2f}\n"
                f"Low: ${low:,.2f}\n"
                f"Volume: {volume:,.0f if volume else 'N/A'}\n"
                f"Number of data points: {len(price_data)}"
            )

            # Get AI analysis
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Using the latest model as of May 13, 2024
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert cryptocurrency analyst. Analyze the provided price data and generate comprehensive insights. 
                        Include: market trend analysis, pattern recognition, support/resistance levels, and trading signals.
                        Respond in JSON format with the following structure:
                        {
                            "trend": string (bullish/bearish/neutral),
                            "trend_strength": string (strong/moderate/weak),
                            "analysis": string (detailed analysis),
                            "patterns": [{"type": string, "confidence": float}],
                            "support_resistance": {"support": float, "resistance": float},
                            "signal": string (BUY/SELL/HOLD),
                            "confidence": float (0-1),
                            "market_sentiment": string
                        }"""
                    },
                    {"role": "user", "content": data_summary}
                ],
                response_format={"type": "json_object"}
            )

            # Parse and return AI analysis
            analysis = response.choices[0].message.content
            return {
                **analysis,
                "price_change_percent": price_change,
                "latest_price": latest_price
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
            # Calculate price movements and volatility
            price_data['returns'] = price_data['close'].pct_change()
            volatility = price_data['returns'].std()

            # Prepare pattern analysis prompt
            data_description = (
                f"Price volatility: {volatility:.4f}\n"
                f"Price trend: {price_data['close'].iloc[-1] - price_data['close'].iloc[0]:.2f}\n"
                f"Number of periods: {len(price_data)}"
            )

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze the price data for common trading patterns. 
                        Return a JSON array of identified patterns with confidence levels.
                        Each pattern should include:
                        {
                            "type": string (pattern name),
                            "confidence": float (0-1),
                            "description": string
                        }"""
                    },
                    {"role": "user", "content": data_description}
                ],
                response_format={"type": "json_object"}
            )

            return response.choices[0].message.content.get("patterns", [])

        except Exception as e:
            logger.error(f"Error in pattern analysis: {str(e)}")
            return []