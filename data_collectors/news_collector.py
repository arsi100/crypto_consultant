import requests
import trafilatura
from typing import List, Dict
from datetime import datetime, timedelta

def get_crypto_news(symbol: str) -> List[Dict]:
    """
    Collect crypto news from multiple sources
    """
    news_items = []

    # NewsAPI endpoint
    news_api_url = "https://newsapi.org/v2/everything"
    params = {
        'q': f"cryptocurrency {symbol}",
        'from': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
        'sortBy': 'popularity',
        'language': 'en',
    }

    try:
        response = requests.get(news_api_url, params=params)
        data = response.json()

        for article in data.get('articles', [])[:10]:
            # Extract clean text content
            if article['url']:
                content = trafilatura.extract(trafilatura.fetch_url(article['url']))
            else:
                content = article['description']

            news_items.append({
                'title': article['title'],
                'summary': article['description'],
                'content': content,
                'url': article['url'],
                'published_at': article['publishedAt'],
                'source': article['source']['name']
            })

    except Exception as e:
        print(f"Error fetching news: {e}")

    return news_items
