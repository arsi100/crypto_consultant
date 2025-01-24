from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import os
from datetime import datetime

Base = declarative_base()

class CachedNews(Base):
    __tablename__ = 'cached_news'

    id = Column(Integer, primary_key=True)
    crypto_symbol = Column(String, nullable=False)
    title = Column(String, nullable=False)
    content = Column(String)
    source = Column(String)
    url = Column(String)
    published_at = Column(DateTime)
    sentiment = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CachedNews(crypto={self.crypto_symbol}, title={self.title})>"

class PriceHistory(Base):
    __tablename__ = 'price_history'

    id = Column(Integer, primary_key=True)
    crypto_symbol = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Float)

    def __repr__(self):
        return f"<PriceHistory(crypto={self.crypto_symbol}, close={self.close_price})>"

class TrendingCoin(Base):
    __tablename__ = 'trending_coins'

    id = Column(Integer, primary_key=True)
    coin_id = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    name = Column(String)
    market_cap_rank = Column(Integer)
    score = Column(Integer)  # Trending score
    price_btc = Column(Float)
    coin_metadata = Column(JSON)  # Store additional coin metadata
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TrendingCoin(symbol={self.symbol}, score={self.score})>"

# Initialize database connection
def init_db():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")

    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine