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

            # Prepare data summary for AI analysis
            data_summary = (
                f"Timeframe: {timeframe}\n"
                f"Latest Price: ${self._format_number(latest_price)}\n"
                f"Price Change: {self._format_number(price_change)}%\n"
                f"High: ${self._format_number(high)}\n"
                f"Low: ${self._format_number(low)}\n"
                f"Volume: {self._format_number(volume, ',.0f')}\n"
                f"Number of data points: {len(price_data)}"
            )

            # Get AI analysis
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert cryptocurrency analyst. Analyze the provided price data and generate comprehensive insights. 
                        Format your response as a valid JSON string with the following structure:
                        {
                            "trend": "bullish/bearish/neutral",
                            "trend_strength": "strong/moderate/weak",
                            "analysis": "detailed analysis text",
                            "patterns": [{"type": "pattern name", "confidence": 0.95}],
                            "support_resistance": {"support": 45000, "resistance": 48000},
                            "signal": "BUY/SELL/HOLD",
                            "confidence": 0.85,
                            "market_sentiment": "bullish/bearish/neutral"
                        }
                        Only respond with the JSON object, no additional text."""
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
                f"Price volatility: {self._format_number(volatility)}\n"
                f"Price trend: {self._format_number(price_data['close'].iloc[-1] - price_data['close'].iloc[0])}\n"
                f"Number of periods: {len(price_data)}"
            )

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze the price data for common trading patterns. 
                        Respond with a valid JSON string in this format:
                        {
                            "patterns": [
                                {
                                    "type": "pattern name",
                                    "confidence": 0.95,
                                    "description": "pattern description"
                                }
                            ]
                        }
                        Only respond with the JSON object, no additional text."""
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