import requests
import trafilatura
from typing import List, Dict
from datetime import datetime, timedelta
import os

def get_crypto_news(symbol: str) -> List[Dict]:
    """
    Collect crypto news from NewsAPI (Free tier - 100 requests/day)
    """
    news_items = []

    # Get API key from environment
    api_key = os.environ.get('NEWS_API_KEY')
    if not api_key:
        print("NewsAPI key not found in environment variables. Please provide a NewsAPI key.")
        return []

    # NewsAPI endpoint
    news_api_url = "https://newsapi.org/v2/everything"
    params = {
        'q': f"cryptocurrency {symbol}",
        'from': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
        'sortBy': 'popularity',
        'language': 'en',
        'pageSize': 10,  # Limit results to conserve daily quota
        'apiKey': api_key
    }

    try:
        response = requests.get(news_api_url, params=params)

        # Handle rate limiting and errors
        if response.status_code == 429:
            print("NewsAPI rate limit reached. Please try again later.")
            return []
        elif response.status_code == 401:
            print("Invalid NewsAPI key. Please check your API key.")
            return []

        response.raise_for_status()
        data = response.json()

        if data.get('status') != 'ok':
            print(f"NewsAPI error: {data.get('message', 'Unknown error')}")
            return []

        for article in data.get('articles', []):
            content = article['description']
            if article['url']:
                try:
                    downloaded = trafilatura.fetch_url(article['url'])
                    if downloaded:
                        extracted = trafilatura.extract(downloaded)
                        if extracted:
                            content = extracted
                except Exception as e:
                    print(f"Error extracting article content: {e}")

            news_items.append({
                'title': article['title'],
                'summary': article['description'],
                'content': content,
                'url': article['url'],
                'published_at': article['publishedAt'],
                'source': article['source']['name']
            })

    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}")
    except Exception as e:
        print(f"Unexpected error in news collection: {e}")

    return news_items