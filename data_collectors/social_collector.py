import requests
from typing import Dict
import pandas as pd
import os
from datetime import datetime, timedelta

def get_social_data(symbol: str) -> Dict:
    """
    Collect social media data from Reddit (Free API) and Twitter (mocked)
    """
    reddit_data = get_reddit_data(symbol)
    twitter_data = get_twitter_data(symbol)

    return {
        'reddit': reddit_data,
        'twitter': twitter_data
    }

def get_reddit_data(symbol: str) -> pd.DataFrame:
    """
    Collect data from Reddit using their API (Free tier)
    """
    client_id = os.environ.get('REDDIT_CLIENT_ID')
    client_secret = os.environ.get('REDDIT_CLIENT_SECRET')

    if not client_id or not client_secret:
        print("Reddit API credentials not found")
        return pd.DataFrame()

    # Get Reddit access token
    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    headers = {'User-Agent': 'CryptoResearchAssistant/1.0'}

    try:
        # Get access token
        token_response = requests.post(
            'https://www.reddit.com/api/v1/access_token',
            auth=auth,
            data={'grant_type': 'client_credentials'},
            headers=headers
        )

        if token_response.status_code != 200:
            print(f"Error getting Reddit token: {token_response.text}")
            return pd.DataFrame()

        token = token_response.json().get('access_token')
        headers['Authorization'] = f'Bearer {token}'

        # Search Reddit
        search_url = f"https://oauth.reddit.com/r/cryptocurrency/search"
        params = {
            'q': symbol,
            't': 'day',
            'sort': 'top',
            'limit': 25  # Reduced limit for free tier
        }

        response = requests.get(search_url, headers=headers, params=params)

        if response.status_code == 429:
            print("Reddit API rate limit reached")
            return pd.DataFrame()

        response.raise_for_status()
        data = response.json()

        posts = []
        for post in data['data']['children']:
            posts.append({
                'title': post['data']['title'],
                'score': post['data']['score'],
                'num_comments': post['data']['num_comments'],
                'created_utc': datetime.fromtimestamp(post['data']['created_utc']),
                'sentiment': 0  # Will be calculated by sentiment analyzer
            })

        return pd.DataFrame(posts)

    except Exception as e:
        print(f"Error fetching Reddit data: {e}")
        return pd.DataFrame()

def get_twitter_data(symbol: str) -> pd.DataFrame:
    """
    Mock Twitter data (until we implement Twitter API)
    """
    current_time = datetime.now()
    mock_data = {
        'text': [
            f"Bullish on {symbol}! 🚀",
            f"Just bought more {symbol}",
            f"{symbol} looking strong today",
        ],
        'likes': [10, 15, 5],
        'retweets': [5, 7, 2],
        'created_at': [
            current_time - timedelta(hours=1),
            current_time - timedelta(hours=2),
            current_time - timedelta(hours=3)
        ],
        'sentiment': [0, 0, 0]  # Will be calculated by sentiment analyzer
    }
    return pd.DataFrame(mock_data)