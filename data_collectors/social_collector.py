import requests
from typing import Dict
import pandas as pd

def get_social_data(symbol: str) -> Dict:
    """
    Collect social media data from Reddit and Twitter
    """
    reddit_data = get_reddit_data(symbol)
    twitter_data = get_twitter_data(symbol)

    return {
        'reddit': reddit_data,
        'twitter': twitter_data
    }

def get_reddit_data(symbol: str) -> pd.DataFrame:
    """
    Collect data from Reddit using their API
    """
    url = f"https://www.reddit.com/r/cryptocurrency/search.json"
    params = {
        'q': symbol,
        't': 'day',
        'sort': 'top',
        'limit': 100
    }

    try:
        response = requests.get(url, params=params, headers={'User-Agent': 'CryptoResearchBot/1.0'})
        data = response.json()

        posts = []
        for post in data['data']['children']:
            posts.append({
                'title': post['data']['title'],
                'score': post['data']['score'],
                'num_comments': post['data']['num_comments'],
                'created_utc': post['data']['created_utc']
            })

        return pd.DataFrame(posts)

    except Exception as e:
        print(f"Error fetching Reddit data: {e}")
        return pd.DataFrame()

def get_twitter_data(symbol: str) -> pd.DataFrame:
    """
    Collect data from Twitter (Note: This is a simplified version due to API limitations)
    """
    # In a real implementation, you would use Twitter API v2
    # This is a mock implementation
    mock_data = {
        'text': [f"Tweet about {symbol}"],
        'likes': [10],
        'retweets': [5],
        'created_at': [pd.Timestamp.now()]
    }
    return pd.DataFrame(mock_data)
