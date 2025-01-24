import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
import requests
from sqlalchemy.orm import Session
from models import TrendingCoin
from database import db

logger = logging.getLogger(__name__)

class TrendingCollector:
    """Collects trending coin data from CoinGecko"""
    
    def __init__(self):
        self.api_key = os.environ.get('COINGECKO_API_KEY')
        if not self.api_key:
            logger.error("CoinGecko API key not found")
            raise ValueError("CoinGecko API key is required")
            
    def fetch_trending_coins(self) -> Optional[List[Dict]]:
        """Fetch trending coins from CoinGecko API"""
        try:
            url = "https://api.coingecko.com/api/v3/search/trending"
            headers = {
                'X-Cg-Api-Key': self.api_key
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 429:
                logger.error("CoinGecko API rate limit reached")
                return None
            elif response.status_code == 401:
                logger.error("Invalid CoinGecko API key")
                return None
                
            response.raise_for_status()
            data = response.json()
            
            return data.get('coins', [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching trending coins: {str(e)}")
            return None
            
    def store_trending_coins(self, trending_data: List[Dict]) -> bool:
        """Store trending coins in the database"""
        try:
            with db.get_session() as session:
                for coin in trending_data:
                    coin_item = coin.get('item', {})
                    trending_coin = TrendingCoin(
                        coin_id=coin_item.get('id'),
                        symbol=coin_item.get('symbol').upper(),
                        name=coin_item.get('name'),
                        market_cap_rank=coin_item.get('market_cap_rank'),
                        price_btc=coin_item.get('price_btc'),
                        score=len(trending_data) - trending_data.index(coin),  # Higher score for higher ranking
                        coin_metadata={
                            'thumb': coin_item.get('thumb'),
                            'small': coin_item.get('small'),
                            'large': coin_item.get('large'),
                            'slug': coin_item.get('slug')
                        },
                        timestamp=datetime.utcnow()
                    )
                    session.add(trending_coin)
                    
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error storing trending coins: {str(e)}")
            return False
            
    def get_latest_trending_coins(self, session: Session, limit: int = 10) -> List[TrendingCoin]:
        """Get the most recent trending coins from database"""
        try:
            return (session.query(TrendingCoin)
                   .order_by(TrendingCoin.timestamp.desc(), TrendingCoin.score.desc())
                   .limit(limit)
                   .all())
        except Exception as e:
            logger.error(f"Error retrieving trending coins: {str(e)}")
            return []

    def update_trending_coins(self) -> bool:
        """Fetch new trending coins and store them in the database"""
        trending_data = self.fetch_trending_coins()
        if trending_data:
            return self.store_trending_coins(trending_data)
        return False
