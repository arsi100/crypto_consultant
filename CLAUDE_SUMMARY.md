# CryptoAI Platform - Project Overview

## Repository Description
An advanced AI-powered cryptocurrency research platform that provides comprehensive market insights through intelligent data aggregation, analysis, and visualization.

Technical Stack:
- Streamlit web interface for interactive data exploration
- Multi-source data collectors (pricing, news, social media)
- CoinGecko API integration for real-time crypto market data
- Machine learning-powered market trend detection and analysis
- Python-based backend with advanced data processing capabilities
- OpenAI integration for market intelligence and trend analysis

## Directory Structure
```
├── analysis/
│   ├── ai_analyzer.py          # AI-powered market analysis using OpenAI
│   ├── pattern_recognition.py  # Technical pattern detection
│   ├── price_analyzer.py       # Price trend analysis
│   └── sentiment_analyzer.py   # News sentiment analysis
├── data_collectors/
│   ├── news_collector.py       # Crypto news aggregation
│   ├── price_collector.py      # Real-time price data collection
│   ├── social_collector.py     # Social media sentiment
│   └── trending_collector.py   # Trending coins tracking
├── utils/
│   ├── data_storage.py        # Analysis results storage
│   └── email_sender.py        # Report delivery system
├── main.py                    # Main Streamlit application
└── models.py                  # Database models
```

## Current Issues Being Fixed

1. Market Overview Section
   - Issue: Only shows signal strength
   - Status: In progress
   - Location: main.py (Market Overview section)

2. Price Analysis Accuracy
   - Issue: Key price points not matching actual Bitcoin prices
   - Location: analysis/price_analyzer.py
   - Status: Being fixed

3. News Integration
   - Issue: Latest news section not displaying data
   - Location: data_collectors/news_collector.py
   - Status: Under investigation

4. Trending Coins
   - Issue: Refresh functionality not working
   - Location: data_collectors/trending_collector.py
   - Status: Being fixed

## Required Environment Variables
```
# API Keys
COINGECKO_API_KEY=your_coingecko_key
OPENAI_API_KEY=your_openai_key
NEWS_API_KEY=your_news_api_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret

# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/dbname
PGDATABASE=your_db_name
PGUSER=your_db_user
PGPASSWORD=your_db_password
PGHOST=your_db_host
PGPORT=your_db_port
```

## Development Status

### Completed Features
- ✅ Interactive Streamlit web interface
- ✅ Real-time price tracking
- ✅ Technical pattern recognition
- ✅ Price chart visualization
- ✅ AI-powered market analysis
- ✅ Support/Resistance level detection
- ✅ Basic sentiment analysis

### In Progress
- 🔄 Market Overview improvements
- 🔄 News aggregation fixes
- 🔄 Trending coins functionality
- 🔄 Market Intelligence section enhancements

### Planned Features
- 📝 Advanced pattern recognition
- 📝 Social media sentiment integration
- 📝 Portfolio tracking
- 📝 Custom alerts system

## Deployment Considerations
Currently running on Replit, but considering migration to a more permanent solution for:
1. Custom domain support
2. 24/7 availability
3. Better scaling capabilities
4. More reliable database persistence

## Questions for Claude
1. Recommendations for fixing the current issues
2. Suggestions for deployment platforms
3. Code review of the current implementation
4. Best practices for real-time data handling
5. Optimization suggestions for API usage
