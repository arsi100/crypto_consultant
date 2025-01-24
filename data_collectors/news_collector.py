import requests
from typing import List, Dict
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger(__name__)

def get_crypto_news(symbol: str) -> List[Dict]:
    """
    Collect crypto news from CoinGecko API
    """
    news_items = []

    # Get API key from environment
    api_key = os.environ.get('COINGECKO_API_KEY', '').strip()
    if not api_key:
        logger.error("CoinGecko API key not found in environment variables")
        return []

    # Convert symbol to CoinGecko coin ID
    coin_mapping = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'BNB': 'binancecoin',
        'XRP': 'ripple',
        'ADA': 'cardano',
        'SOL': 'solana',
        'DOT': 'polkadot',
        'DOGE': 'dogecoin',
        'MATIC': 'matic-network',
        'LINK': 'chainlink'
    }

    coin_id = coin_mapping.get(symbol.upper())
    if not coin_id:
        logger.error(f"Unsupported coin symbol: {symbol}")
        return []

    # CoinGecko API endpoint for news
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/news"

    headers = {
        'x-cg-api-key': api_key  # Changed to lowercase as per CoinGecko's requirements
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 429:
            logger.error("CoinGecko API rate limit reached")
            return []
        elif response.status_code == 401:
            logger.error("Invalid CoinGecko API key")
            return []
        elif response.status_code == 404:
            # Fallback to general news endpoint if coin-specific news not found
            url = "https://api.coingecko.com/api/v3/news"
            response = requests.get(url, headers=headers, timeout=10)

        response.raise_for_status()
        data = response.json()

        # Process news items
        for item in data[:10]:  # Limit to 10 most recent news items
            news_items.append({
                'title': item.get('title', ''),
                'summary': item.get('description', ''),
                'content': item.get('text', ''),
                'url': item.get('url', ''),
                'published_at': item.get('published_at', ''),
                'source': item.get('author', 'CoinGecko')
            })

        return news_items

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching news from CoinGecko: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in news collection: {str(e)}")
        return []