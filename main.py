import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import os
import time
import json
import logging
import requests # Added missing import for requests
from data_collectors.price_collector import get_crypto_prices
from data_collectors.news_collector import get_crypto_news
from data_collectors.social_collector import get_social_data
from data_collectors.trending_collector import TrendingCollector
from analysis.price_analyzer import analyze_price_trends
from analysis.sentiment_analyzer import analyze_sentiment
from utils.email_sender import send_daily_report
from utils.data_storage import store_analysis_results
from database import db  # Add the missing import

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

def apply_tradingview_style():
    """Apply TradingView-inspired dark theme"""
    st.markdown("""
        <style>
        /* Basic theme colors */
        .main {
            color: #d1d4dc;
            background-color: #1e222d;
        }

        .stApp {
            background-color: #1e222d;
        }

        /* Sidebar styling */
        .css-1d391kg {  /* Streamlit's sidebar class */
            width: 14rem !important;
        }

        /* Container styling */
        .tradingview-widget-container {
            background-color: #2a2e39;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border: 1px solid #363c4e;
            overflow-wrap: break-word;
            word-wrap: break-word;
            word-break: break-word;
        }

        .price-display {
            font-size: 2rem;
            margin: 0.5rem 0;
            overflow-wrap: break-word;
            word-wrap: break-word;
            word-break: break-word;
            max-width: 100%;
            display: inline-block;
        }

        .indicator-panel {
            background-color: #2a2e39;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #363c4e;
            margin-bottom: 1rem;
        }

        .news-panel {
            background-color: #2a2e39;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #363c4e;
            margin-bottom: 1rem;
        }

        /* Button styling */
        .stButton>button {
            background-color: #2962ff;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
        }

        /* Text styling */
        h1, h2, h3 {
            color: #d1d4dc !important;
        }

        .stMarkdown {
            color: #d1d4dc;
        }

        /* SelectBox styling */
        .stSelectbox > div > div {
            max-width: 200px;
        }
        </style>
    """, unsafe_allow_html=True)

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

def display_price_widget(price_data, coin):
    """Display current price in TradingView style with improved text wrapping"""
    if price_data:
        price = price_data['price']
        change = price_data['change_24h']
        color = "color: #26a69a" if change > 0 else "color: #ef5350"

        st.markdown(f"""
        <div class="tradingview-widget-container">
            <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                <h3 style="color: #d1d4dc; margin: 0;">{AVAILABLE_COINS[coin]['name']} ({coin})</h3>
                <div class="price-display" style="{color}">
                    ${price:,.2f}
                </div>
                <div style="{color}">
                    {change:+.2f}% (24h)
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("Unable to fetch price data")

def display_trend_detection(price_analysis):
    """Display trend detection with more user-friendly language"""
    if price_analysis:
        st.markdown("""
        <div class="tradingview-widget-container">
            <h4 style="color: #d1d4dc;">💡 Market Summary</h4>
        """, unsafe_allow_html=True)

        # Convert technical analysis to more casual language
        analysis = price_analysis.get('analysis', '')
        analysis = analysis.replace('Head and Shoulders', 'reversal pattern')
        analysis = analysis.replace('technical indicators', 'market signals')
        analysis = analysis.replace('resistance levels', 'price ceilings')
        analysis = analysis.replace('support levels', 'price floors')
        analysis = analysis.replace('bullish', 'upward')
        analysis = analysis.replace('bearish', 'downward')

        st.markdown(f"""
            <div style="color: #d1d4dc; margin-bottom: 1rem; font-size: 1.1rem; line-height: 1.5;">
                {analysis}
            </div>
        """, unsafe_allow_html=True)

        # Show key price levels in a more friendly way
        if 'support_resistance' in price_analysis:
            sr_levels = price_analysis['support_resistance']
            if isinstance(sr_levels.get('support'), (list, tuple)) and isinstance(sr_levels.get('resistance'), (list, tuple)):
                st.markdown("""
                <h4 style="color: #d1d4dc; margin-top: 1rem;">🎯 Key Price Points</h4>
                """, unsafe_allow_html=True)

                support_levels = sr_levels['support']
                resistance_levels = sr_levels['resistance']

                # Only show the first two levels
                for i, (support, resistance) in enumerate(zip(support_levels[:2], resistance_levels[:2])):
                    st.markdown(f"""
                    <div style="color: #d1d4dc; margin: 0.5rem 0;">
                        <div style="display: flex; justify-content: space-between;">
                            <span>Price Floor #{i+1}:</span>
                            <span style="color: #26a69a">${support:,.2f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>Price Ceiling #{i+1}:</span>
                            <span style="color: #ef5350">${resistance:,.2f}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

def display_trending_coins():
    """Display trending coins section"""
    st.markdown("""
    <div class="tradingview-widget-container">
        <h3 style="color: #d1d4dc;">🔥 Trending Coins</h3>
    </div>
    """, unsafe_allow_html=True)

    try:
        # Initialize trending collector
        trending_collector = TrendingCollector()

        # Add refresh button with improved styling
        col1, col2 = st.columns([1, 4])
        with col1:
            refresh_clicked = st.button("🔄 Refresh", key="refresh_trending", help="Update trending coins data")

        if refresh_clicked:
            with st.spinner("Getting fresh market trends..."):
                trending_collector.update_trending_coins()

        # Get trending coins using a database session
        with db.get_session() as session:
            trending_coins = trending_collector.get_latest_trending_coins(session)

            if trending_coins:
                for coin in trending_coins:
                    with st.expander(f"#{coin.market_cap_rank} {coin.name} ({coin.symbol.upper()})", expanded=False):
                        col1, col2 = st.columns([1, 3])

                        with col1:
                            if coin.coin_metadata and 'small' in coin.coin_metadata:
                                st.image(coin.coin_metadata['small'], width=50)

                        with col2:
                            color = "#26a69a" if coin.score > 0.5 else "#ef5350"
                            st.markdown(f"""
                            <div style="color: #d1d4dc; padding: 0.5rem;">
                                <div style="margin-bottom: 0.5rem;">
                                    <strong>Rank:</strong> {coin.market_cap_rank if coin.market_cap_rank else 'N/A'}
                                </div>
                                <div style="margin-bottom: 0.5rem;">
                                    <strong>Price:</strong> ₿ {coin.price_btc:.8f}
                                </div>
                                <div style="margin-bottom: 0.5rem; color: {color};">
                                    <strong>Trending Score:</strong> {coin.score:.2f}
                                </div>
                                <div style="font-size: 0.8rem; color: #666;">
                                    Updated: {coin.timestamp.strftime('%I:%M %p UTC')}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info("👀 No trending coins yet. Hit refresh to see what's hot!")

    except Exception as e:
        logger.error(f"Error in trending coins section: {str(e)}")
        st.error("Unable to load trending coins. Please try refreshing in a moment.")

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

def json_serial(obj):
    if isinstance(obj, (datetime, pd.Timestamp)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def display_news_section(crypto):
    """Display news with sentiment analysis"""
    try:
        # Add loading state
        with st.spinner('Fetching latest news...'):
            news = get_crypto_news(crypto)

            if news:
                # Get sentiment analysis
                sentiment = analyze_sentiment(news)

                for item in news[:5]:  # Display top 5 news items
                    # Determine sentiment icon
                    sentiment_color = (
                        "🟢" if item.get('sentiment') == 'positive'
                        else "🔴" if item.get('sentiment') == 'negative'
                        else "⚪"
                    )

                    with st.expander(f"{sentiment_color} {item['title']}"):
                        st.markdown(f"""
                        <div style='color: #d1d4dc;'>
                            {item.get('summary', 'No summary available')}
                            <br><br>
                            <small>Source: {item.get('source', 'Unknown')} • 
                            Published: {item.get('published_at', 'N/A')}</small>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No recent news available. Please try again later.")
    except Exception as e:
        st.error(f"Unable to fetch news at the moment. Please try again later.")
        logger.error(f"Error in display_news_section: {str(e)}")

def chat_interface():
    """Display chat interface for user queries"""
    st.subheader("💬 Chat Assistant")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_question = st.text_input(
        "Ask about market trends, technical analysis, or news impact:",
        key="chat_input"
    )

    if user_question:
        if st.session_state.current_coin and st.session_state.price_analysis:
            response = f"Analysis for {st.session_state.current_coin}:\n\n"

            # Add price analysis
            if 'trend' in st.session_state.price_analysis:
                response += f"📈 Current Trend: {st.session_state.price_analysis['trend'].title()}\n"
                response += f"💪 Trend Strength: {st.session_state.price_analysis['trend_strength'].title()}\n\n"

            # Add technical indicators
            if 'indicators' in st.session_state.price_analysis:
                indicators = st.session_state.price_analysis['indicators']
                response += "Technical Indicators:\n"
                for indicator, value in indicators.items():
                    response += f"• {indicator.upper()}: {value}\n"

            st.write(response)
            st.session_state.chat_history.append((user_question, response))
        else:
            st.warning("Please select a cryptocurrency first to get analysis.")


def main():
    st.set_page_config(layout="wide", page_title="CryptoAI Platform", page_icon="📈")
    apply_tradingview_style()

    # Check for required API keys
    if not os.environ.get('COINGECKO_API_KEY'):
        st.error("CoinGecko API key is missing. Please add it to continue.")
        return

    # Initialize session state
    if 'current_coin' not in st.session_state:
        st.session_state.current_coin = "BTC"
    if 'price_analysis' not in st.session_state:
        st.session_state.price_analysis = None

    # Sidebar controls
    with st.sidebar:
        st.title("📊 Controls")
        coin_options = {f"{symbol} - {info['name']}": symbol
                      for symbol, info in AVAILABLE_COINS.items()}
        selected_display = st.selectbox(
            "Select Cryptocurrency",
            options=list(coin_options.keys()),
            key='coin_selector'
        )
        selected_coin = coin_options[selected_display]
        st.session_state.current_coin = selected_coin
        timeframe = st.selectbox(
            "Timeframe",
            ["24h", "7d", "30d"],
            key='timeframe_selector'
        )

    st.title("CryptoAI Platform")

    # Get price data and analysis
    price_data = get_real_crypto_price(st.session_state.current_coin)
    historical_prices = get_crypto_prices(st.session_state.current_coin, timeframe)

    if historical_prices is not None and not historical_prices.empty:
        st.session_state.price_analysis = analyze_price_trends(historical_prices)
    else:
        st.session_state.price_analysis = None

    # Top section layout
    col1, col2, col3 = st.columns([2, 2, 3])

    with col1:
        st.markdown("### Price")
        display_price_widget(price_data, st.session_state.current_coin)

        # Move analysis here
        if st.session_state.price_analysis:
            st.markdown("""
            <div style="height: 20px;"></div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="indicator-panel">
                <h4 style="color: #d1d4dc;">Price Analysis</h4>
                <div style="color: #d1d4dc;">
                    {st.session_state.price_analysis.get('analysis', 'Analysis not available')}
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("### Market Overview")
        if st.session_state.price_analysis:
            signal = st.session_state.price_analysis.get('signal', 'HOLD')
            signal_color = "#26a69a" if signal == "BUY" else "#ef5350" if signal == "SELL" else "#888888"

            st.markdown(f"""
            <div class="indicator-panel">
                <h4 style="color: #d1d4dc;">Signal Strength</h4>
                <div style="color: {signal_color}; font-size: 1.2rem;">{signal}</div>
                <div style="color: #d1d4dc; font-size: 0.9rem;">
                    Confidence: {st.session_state.price_analysis.get('confidence', 0)*100:.0f}%
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col3:
        st.markdown("### Trend Detection")
        display_trend_detection(st.session_state.price_analysis)

    # Price Chart and Analysis Section
    st.markdown("---")
    chart_col, news_col = st.columns([3, 2])

    with chart_col:
        st.markdown("### Price Chart")
        display_price_chart(st.session_state.current_coin, timeframe)

        # Technical Indicators
        if st.session_state.price_analysis and st.session_state.price_analysis.get('indicators'):
            st.markdown("### Technical Indicators")
            indicators = st.session_state.price_analysis['indicators']
            for name, value in indicators.items():
                if value is not None:
                    st.metric(
                        label=name.upper(),
                        value=f"{value:.2f}" if isinstance(value, float) else value
                    )

    with news_col:
        st.markdown("### Latest News")
        display_news_section(st.session_state.current_coin)

    # Add Trending Coins Section
    st.markdown("---")
    display_trending_coins()

    # Market Intelligence Section
    st.markdown("---")
    intel_col1, intel_col2 = st.columns([4, 1])

    with intel_col1:
        st.markdown("### Market Intelligence")
        if st.session_state.price_analysis:
            sentiment = st.session_state.price_analysis.get('market_sentiment', 'Neutral')
            st.markdown(f"""
            <div class="indicator-panel">
                <h4 style="color: #d1d4dc;">Market Overview</h4>
                <div style="color: #d1d4dc;">
                    <p>Current Market Sentiment: {sentiment}</p>
                    <p>24h Price Change: {st.session_state.price_analysis.get('price_change_percent', 0):.2f}%</p>
                </div>
            """, unsafe_allow_html=True)

            if 'support_resistance' in st.session_state.price_analysis:
                sr_levels = st.session_state.price_analysis['support_resistance']
                if sr_levels['support']:
                    st.write(f"Support level: ${sr_levels['support']:,.2f}")
                if sr_levels['resistance']:
                    st.write(f"Resistance level: ${sr_levels['resistance']:,.2f}")

            st.markdown("</div>", unsafe_allow_html=True)

    with intel_col2:
        if st.button("Generate Report", key="single_report_btn"):
            try:
                with st.spinner("Generating comprehensive analysis..."):
                    success, message = generate_daily_report(
                        st.session_state.current_coin,
                        st.session_state.price_analysis,
                        get_crypto_news(st.session_state.current_coin),
                        analyze_sentiment(get_crypto_news(st.session_state.current_coin))
                    )
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")

    # Chat Interface Section
    st.markdown("---")
    chat_interface()


if __name__ == "__main__":
    main()