import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import os
import time
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper function for JSON serialization
def json_serial(obj):
    if isinstance(obj, (datetime, pd.Timestamp)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

from data_collectors.price_collector import get_crypto_prices
from data_collectors.news_collector import get_crypto_news
from data_collectors.social_collector import get_social_data
from analysis.price_analyzer import analyze_price_trends
from analysis.sentiment_analyzer import analyze_sentiment
from utils.email_sender import send_daily_report
from utils.data_storage import store_analysis_results

# Configure Streamlit page
st.set_page_config(
    page_title="AI Crypto Research Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for data persistence
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.chat_input = ""
    st.session_state.last_update = None
    st.session_state.error_count = 0
    st.session_state.max_retries = 3
    st.session_state.trends = None
    st.session_state.news = []
    st.session_state.sentiment = {'overall': 'neutral'}
    st.session_state.social_data = {'reddit': pd.DataFrame(), 'twitter': pd.DataFrame()}

def initialize_app():
    """Initialize the application and handle any startup requirements"""
    try:
        if not st.session_state.initialized:
            logger.info("Initializing application...")
            st.session_state.initialized = True
            st.session_state.last_update = datetime.now()
            logger.info("Application initialized successfully")
            return True
    except Exception as e:
        logger.error(f"Error initializing application: {str(e)}")
        st.error(f"Error initializing application: {str(e)}")
        return False

def main():
    try:
        st.title("🤖 AI Crypto Research Assistant")

        # Sidebar controls
        st.sidebar.title("Controls")
        crypto = st.sidebar.selectbox(
            "Select Cryptocurrency",
            ["BTC", "ETH", "BNB", "XRP", "ADA"]
        )

        timeframe = st.sidebar.selectbox(
            "Select Timeframe",
            ["24h", "7d", "30d"]
        )

        logger.info(f"Selected crypto: {crypto}, timeframe: {timeframe}")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Price Analysis")
            price_placeholder = st.empty()

            try:
                with price_placeholder:
                    logger.info("Fetching price data...")
                    st.info("Fetching price data...")
                    prices = get_crypto_prices(crypto, timeframe)

                    if prices is None:
                        logger.error("Price data is None")
                        st.error("Failed to fetch price data. Please try again.")
                        return

                    if prices.empty:
                        logger.error("Empty price dataframe received")
                        st.error("No price data available. The API may be experiencing issues.")
                        return

                    logger.info(f"Successfully fetched price data: {len(prices)} records")

                    # Display current price prominently
                    current_price = prices['close'].iloc[-1]
                    last_updated = prices['timestamp'].iloc[-1].strftime("%Y-%m-%d %H:%M:%S UTC")

                    st.markdown(f"""
                    <div style='padding: 1rem; background-color: #1E1E1E; border-radius: 10px; margin-bottom: 1rem;'>
                        <h2 style='margin: 0; color: #E0E0E0;'>{crypto} Current Price</h2>
                        <h1 style='margin: 0.5rem 0; color: #00FF00;'>${current_price:,.2f}</h1>
                        <p style='margin: 0; color: #808080; font-size: 0.8rem;'>Last Updated: {last_updated}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Create price chart
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=prices['timestamp'],
                        open=prices['open'],
                        high=prices['high'],
                        low=prices['low'],
                        close=prices['close']
                    ))
                    fig.update_layout(
                        title=f"{crypto} Price Chart ({timeframe})",
                        yaxis_title="Price (USD)",
                        xaxis_title="Time",
                        template="plotly_dark"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Show trend analysis
                    logger.info("Analyzing price trends...")
                    st.session_state.trends = analyze_price_trends(prices)

                    if st.session_state.trends is None:
                        logger.error("Trend analysis returned None")
                        st.error("Error analyzing price trends")
                        return

                    st.markdown("### Trend Analysis")
                    col_trend1, col_trend2 = st.columns(2)

                    with col_trend1:
                        st.write("**Current Trend:**", st.session_state.trends['trend'].capitalize())
                        st.write("**Trend Strength:**", st.session_state.trends['trend_strength'].capitalize())
                        if st.session_state.trends['price_change_percent'] != 0:
                            st.write("**Price Change:**", f"{st.session_state.trends['price_change_percent']}%")

                    with col_trend2:
                        if st.session_state.trends['indicators']['rsi'] is not None:
                            st.write("**RSI:**", st.session_state.trends['indicators']['rsi'])
                        if st.session_state.trends['support_resistance']['support'] is not None:
                            st.write("**Support Level:**", st.session_state.trends['support_resistance']['support'])
                        if st.session_state.trends['support_resistance']['resistance'] is not None:
                            st.write("**Resistance Level:**", st.session_state.trends['support_resistance']['resistance'])

                    st.write("**Analysis:**", st.session_state.trends['analysis'])

            except Exception as e:
                logger.error(f"Error in price analysis section: {str(e)}", exc_info=True)
                st.error(f"Error in price analysis: {str(e)}")

        with col2:
            st.subheader("News & Sentiment")
            try:
                if not os.environ.get('NEWS_API_KEY'):
                    logger.warning("NewsAPI key is missing")
                    st.warning("NewsAPI key is missing. Please add your NewsAPI key to fetch news data.")
                else:
                    logger.info("Fetching news data...")
                    st.session_state.news = get_crypto_news(crypto)

                    if st.session_state.news:
                        logger.info(f"Successfully fetched {len(st.session_state.news)} news items")
                        try:
                            st.session_state.sentiment = analyze_sentiment(st.session_state.news)
                            logger.info(f"Sentiment analysis completed: {st.session_state.sentiment['overall']}")
                        except Exception as e:
                            logger.error(f"Error analyzing sentiment: {str(e)}")
                            st.session_state.sentiment = {'overall': 'neutral'}

                        st.markdown("### Latest News")
                        for item in st.session_state.news[:5]:
                            with st.expander(item['title']):
                                st.markdown(f"_{item.get('summary', 'No summary available')}_")
                                sentiment_color = (
                                    "🟢" if item.get('sentiment') == 'positive'
                                    else "🔴" if item.get('sentiment') == 'negative'
                                    else "⚪"
                                )
                                st.markdown(f"Sentiment: {sentiment_color} {item.get('sentiment', 'neutral')}")
                    else:
                        logger.warning("No news data found")
                        st.warning("No recent news found for this cryptocurrency.")
            except Exception as e:
                logger.error(f"Error in news section: {str(e)}", exc_info=True)
                st.error(f"Error fetching news: {str(e)}")

        # Chat Interface
        st.subheader("Chat with Assistant")
        user_question = st.text_input(
            "Ask me anything about the current crypto market:",
            key="chat_input"
        )

        if user_question:
            try:
                logger.info(f"Processing chat question: {user_question}")
                response = "Based on the current analysis:\n\n"

                if st.session_state.trends:
                    response += f"📈 {crypto} Price Analysis:\n"
                    response += f"• Current trend: {st.session_state.trends['trend'].capitalize()}\n"
                    response += f"• {st.session_state.trends['analysis']}\n\n"

                    if st.session_state.trends['indicators']['rsi'] is not None:
                        rsi_val = st.session_state.trends['indicators']['rsi']
                        response += f"• RSI Analysis: {rsi_val:.1f} - "
                        if rsi_val > 70:
                            response += "Market is overbought, potential reversal incoming\n"
                        elif rsi_val < 30:
                            response += "Market is oversold, watch for potential upward movement\n"
                        else:
                            response += "RSI in neutral territory\n"

                if st.session_state.news:
                    response += "\n📰 News Sentiment:\n"
                    response += f"• Overall market sentiment: {st.session_state.sentiment.get('overall', 'neutral').capitalize()}\n"
                    response += "• Key news impacts:\n"
                    for item in st.session_state.news[:3]:
                        response += f"  - {item['title']}\n"
                        response += f"    Sentiment: {item.get('sentiment', 'neutral').capitalize()}\n"

                logger.info("Generated chat response successfully")
                st.write(response)
            except Exception as e:
                logger.error(f"Error generating chat response: {str(e)}", exc_info=True)
                st.error(f"Error generating response: {str(e)}")

        # Generate and store daily report
        if st.button("Generate Daily Report"):
            logger.info("Starting report generation...")
            with st.spinner('Generating report...'):
                try:
                    if not st.session_state.trends:
                        logger.error("No price analysis data available for report")
                        st.error("No price analysis data available. Please wait for data to load.")
                        return

                    report_data = {
                        'timestamp': datetime.now(),
                        'crypto': crypto,
                        'price_analysis': {
                            'trend': st.session_state.trends.get('trend', 'unknown'),
                            'strength': st.session_state.trends.get('trend_strength', 'unknown'),
                            'analysis': st.session_state.trends.get('analysis', 'No analysis available'),
                            'indicators': st.session_state.trends.get('indicators', {})
                        },
                        'news_sentiment': st.session_state.sentiment.get('overall', 'neutral'),
                        'news_items': [
                            {
                                'title': item.get('title', ''),
                                'sentiment': item.get('sentiment', 'neutral'),
                                'summary': item.get('summary', '')
                            }
                            for item in st.session_state.news[:5]
                        ] if st.session_state.news else []
                    }

                    logger.info("Converting report data to JSON...")
                    serialized_data = json.loads(json.dumps(report_data, default=json_serial))

                    logger.info("Storing analysis results...")
                    store_analysis_results(serialized_data)

                    logger.info("Sending daily report...")
                    send_daily_report(serialized_data)

                    logger.info("Report generated and sent successfully")
                    st.success("Daily report generated and sent successfully!")

                except Exception as e:
                    logger.error(f"Error in report generation: {str(e)}", exc_info=True)
                    st.error(f"Error generating report: {str(e)}")

    except Exception as e:
        logger.error(f"Main application error: {str(e)}", exc_info=True)
        st.error(f"Application error: {str(e)}")
        st.info("Please try refreshing the page. If the error persists, contact support.")

if __name__ == "__main__":
    try:
        if initialize_app():
            main()
    except Exception as e:
        logger.error(f"Application startup error: {str(e)}", exc_info=True)
        st.error(f"Application error: {str(e)}")
        st.info("Please try refreshing the page. If the error persists, contact support.")