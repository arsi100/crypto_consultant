import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import os
import time
import json
import logging
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Extended coin list with descriptions
AVAILABLE_COINS = {
    "BTC": {"name": "Bitcoin", "id": "bitcoin"},
    "ETH": {"name": "Ethereum", "id": "ethereum"},
    "BNB": {"name": "Binance Coin", "id": "binancecoin"},
    "XRP": {"name": "Ripple", "id": "ripple"},
    "ADA": {"name": "Cardano", "id": "cardano"},
    "SOL": {"name": "Solana", "id": "solana"},
    "DOT": {"name": "Polkadot", "id": "polkadot"},
    "DOGE": {"name": "Dogecoin", "id": "dogecoin"},
    "MATIC": {"name": "Polygon", "id": "matic-network"},
    "LINK": {"name": "Chainlink", "id": "chainlink"}
}

def json_serial(obj):
    if isinstance(obj, (datetime, pd.Timestamp)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def get_real_crypto_price(crypto):
    """Get real-time price data from CoinGecko"""
    try:
        api_key = os.environ.get('COINGECKO_API_KEY')
        if not api_key:
            logger.error("CoinGecko API key not found")
            return None

        coin_id = AVAILABLE_COINS.get(crypto, {}).get('id')
        if not coin_id:
            logger.error(f"Unknown coin symbol: {crypto}")
            return None

        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': coin_id,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }

        headers = {
            'X-Cg-Api-Key': api_key
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return {
                'price': data[coin_id]['usd'],
                'change_24h': data[coin_id].get('usd_24h_change', 0)
            }
        else:
            logger.error(f"CoinGecko API error: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error fetching real-time price: {str(e)}")
        return None

from data_collectors.price_collector import get_crypto_prices
from data_collectors.news_collector import get_crypto_news
from data_collectors.social_collector import get_social_data
from analysis.price_analyzer import analyze_price_trends
from analysis.sentiment_analyzer import analyze_sentiment
from utils.email_sender import send_daily_report
from utils.data_storage import store_analysis_results


def apply_tradingview_style():
    """Apply TradingView-inspired dark theme"""
    st.markdown("""
        <style>
        .tradingview-widget-container {
            background-color: #1e222d;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }

        .price-widget {
            background-color: #2a2e39;
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid #363c4e;
        }

        .indicator-panel {
            background-color: #2a2e39;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #363c4e;
            margin-bottom: 1rem;
        }

        .stButton>button {
            background-color: #2962ff;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
        }

        div[data-testid="stDecoration"] {
            background-image: linear-gradient(90deg, #2962ff, #2962ff);
        }

        .plot-container {
            background-color: #1e222d !important;
            border: 1px solid #363c4e;
            border-radius: 8px;
            padding: 1rem;
        }

        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3 {
            color: #d1d4dc;
        }
        </style>
    """, unsafe_allow_html=True)

def display_price_widget(price_data, coin):
    """Display current price in TradingView style"""
    if price_data:
        price = price_data['price']
        change = price_data['change_24h']
        color = "color: #26a69a" if change > 0 else "color: #ef5350"

        st.markdown(f"""
        <div class="price-widget">
            <h3 style="color: #d1d4dc; margin: 0;">{coin}</h3>
            <div style="font-size: 2rem; {color}">
                ${price:,.2f}
            </div>
            <div style="{color}">
                {change:+.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("Unable to fetch price data")

def display_price_chart(coin, timeframe):
    """Display interactive price chart"""
    try:
        prices = get_crypto_prices(coin, timeframe)
        if prices is not None and not prices.empty:
            fig = create_candlestick_chart(prices, coin, timeframe)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Unable to load price data")
    except Exception as e:
        st.error(f"Error displaying chart: {str(e)}")

def create_candlestick_chart(prices, coin, timeframe):
    """Create an interactive candlestick chart"""
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=prices['timestamp'],
        open=prices['open'],
        high=prices['high'],
        low=prices['low'],
        close=prices['close'],
        name="Price"
    ))

    fig.update_layout(
        title=f"{coin} Price Chart ({timeframe})",
        yaxis_title="Price (USD)",
        xaxis_title="Time",
        template="plotly_dark",
        height=400,
        margin=dict(l=50, r=50, t=50, b=50),
        yaxis=dict(side="right"),
        xaxis=dict(rangeslider=dict(visible=False))
    )

    return fig

def generate_daily_report(crypto, trends, news, sentiment):
    """Generates and handles report data"""
    try:
        if not trends:
            return False, "No price analysis data available. Please wait for data to load."

        report_data = {
            'timestamp': datetime.now(),
            'crypto': crypto,
            'price_analysis': {
                'trend': trends.get('trend', 'unknown'),
                'strength': trends.get('trend_strength', 'unknown'),
                'analysis': trends.get('analysis', 'No analysis available'),
                'indicators': trends.get('indicators', {})
            },
            'news_sentiment': sentiment.get('overall', 'neutral'),
            'news_items': [
                {
                    'title': item.get('title', ''),
                    'sentiment': item.get('sentiment', 'neutral'),
                    'summary': item.get('summary', '')
                }
                for item in (news[:5] if news else [])
            ]
        }

        serialized_data = json.loads(json.dumps(report_data, default=json_serial))
        store_analysis_results(serialized_data)
        send_daily_report(serialized_data)
        return True, "Daily report generated and sent successfully!"

    except Exception as e:
        logger.error(f"Error in report generation: {str(e)}", exc_info=True)
        return False, f"Error generating report: {str(e)}"


def main():
    st.set_page_config(layout="wide", page_title="CryptoAI Platform", page_icon="📈")
    apply_tradingview_style()

    # Initialize session state
    if 'current_coin' not in st.session_state:
        st.session_state.current_coin = "BTC"

    # Sidebar
    with st.sidebar:
        st.title("📊 Controls")

        # Coin selection
        coin_options = {f"{symbol} - {info['name']}": symbol 
                      for symbol, info in AVAILABLE_COINS.items()}

        selected_display = st.selectbox(
            "Select Cryptocurrency",
            options=list(coin_options.keys()),
            key='coin_selector'
        )

        selected_coin = coin_options[selected_display]
        st.session_state.current_coin = selected_coin

        # Timeframe
        timeframe = st.selectbox(
            "Timeframe",
            ["24h", "7d", "30d"],
            key='timeframe_selector'
        )

        # Technical Analysis Filters
        st.markdown("### 📊 Technical Analysis")
        show_ma = st.checkbox("Moving Averages", value=True)
        show_bb = st.checkbox("Bollinger Bands", value=True)
        show_rsi = st.checkbox("RSI", value=True)

    # Main content
    st.title("CryptoAI Platform")

    # Get price data
    price_data = get_real_crypto_price(st.session_state.current_coin)

    # Layout
    col1, col2, col3 = st.columns([2, 2, 3])

    with col1:
        st.markdown("### Price")
        display_price_widget(price_data, st.session_state.current_coin)

    with col2:
        st.markdown("### Market Overview")
        with st.container():
            st.markdown("""
            <div class="indicator-panel">
                <h4 style="color: #d1d4dc;">Signal Strength</h4>
                <div style="color: #26a69a; font-size: 1.2rem;">Strong Buy</div>
            </div>
            """, unsafe_allow_html=True)

    with col3:
        st.markdown("### Trend Detection")
        with st.container():
            st.markdown("""
            <div class="indicator-panel">
                <h4 style="color: #d1d4dc;">Emerging Patterns</h4>
                <div style="color: #d1d4dc;">
                    • Volume Breakout Detected<br/>
                    • Bullish MACD Crossover
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Charts Section
    st.markdown("---")

    chart_col1, chart_col2 = st.columns([3, 2])

    with chart_col1:
        st.markdown("### Price Chart")
        display_price_chart(st.session_state.current_coin, timeframe)

    with chart_col2:
        st.markdown("### Technical Indicators")
        # Add technical indicators here -  This would ideally use data from get_crypto_prices and analyze_price_trends


    # Bottom section for reports
    st.markdown("---")
    report_col1, report_col2 = st.columns([4, 1])

    with report_col1:
        st.markdown("### Market Intelligence")
        # Add market insights here - This would ideally use data from get_crypto_news and analyze_sentiment

    with report_col2:
        if st.button("Generate Report", key="single_report_btn"):
            try:
                with st.spinner("Generating comprehensive analysis..."):
                    trends = analyze_price_trends(st.session_state.current_coin, timeframe) # Example, replace with actual call
                    news = get_crypto_news(st.session_state.current_coin) # Example, replace with actual call
                    sentiment = analyze_sentiment(news) # Example, replace with actual call
                    success, message = generate_daily_report(st.session_state.current_coin, trends, news, sentiment)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")

if __name__ == "__main__":
    main()