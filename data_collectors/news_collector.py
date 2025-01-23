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
    api_key = os.environ.get('COINGECKO_API_KEY')
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
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/status_updates"

    headers = {
        'X-Cg-Api-Key': api_key
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 429:
            logger.error("CoinGecko API rate limit reached")
            return []
        elif response.status_code == 401:
            logger.error("Invalid CoinGecko API key")
            return []

        response.raise_for_status()
        data = response.json()

        # Process status updates (news)
        for update in data.get('status_updates', [])[:10]:  # Limit to 10 most recent updates
            news_items.append({
                'title': update.get('description', '').split('\n')[0],  # First line as title
                'summary': update.get('description', ''),
                'content': update.get('description', ''),
                'url': update.get('project', {}).get('link', ''),
                'published_at': update.get('created_at', ''),
                'source': 'CoinGecko'
            })

        # If we have space for more news, fetch from the markets endpoint
        if len(news_items) < 10:
            market_url = "https://api.coingecko.com/api/v3/news"
            market_response = requests.get(market_url, headers=headers, timeout=10)

            if market_response.status_code == 200:
                market_news = market_response.json()
                for article in market_news[:10 - len(news_items)]:
                    if coin_id.lower() in article.get('title', '').lower():
                        news_items.append({
                            'title': article.get('title', ''),
                            'summary': article.get('description', ''),
                            'content': article.get('text', ''),
                            'url': article.get('url', ''),
                            'published_at': article.get('published_at', ''),
                            'source': article.get('author', 'CoinGecko')
                        })

        return news_items

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching news from CoinGecko: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in news collection: {str(e)}")
        return []