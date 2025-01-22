import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import os
import time

from data_collectors.price_collector import get_crypto_prices
from data_collectors.news_collector import get_crypto_news
from data_collectors.social_collector import get_social_data
from analysis.price_analyzer import analyze_price_trends
from analysis.sentiment_analyzer import analyze_sentiment
from utils.email_sender import send_daily_report
from utils.data_storage import store_analysis_results

# Configure Streamlit page
st.set_page_config(
    page_title="Crypto Research Assistant",
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

def initialize_app():
    """Initialize the application and handle any startup requirements"""
    try:
        if not st.session_state.initialized:
            # Any initialization code here
            st.session_state.initialized = True
            st.session_state.last_update = datetime.now()
            return True
    except Exception as e:
        st.error(f"Error initializing application: {str(e)}")
        return False

def main():
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

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Price Analysis")
        price_placeholder = st.empty()
        trends = analyze_price_trends(pd.DataFrame())  # Initialize with default values

        try:
            with price_placeholder:
                with st.spinner('Fetching price data...'):
                    st.info("Connecting to CoinGecko API...")
                    prices = get_crypto_prices(crypto, timeframe)

                    if not prices.empty:
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
                        trends = analyze_price_trends(prices)
                        st.markdown("### Trend Analysis")

                        # Display trend analysis in a more readable format
                        col_trend1, col_trend2 = st.columns(2)
                        with col_trend1:
                            st.write("**Current Trend:**", trends['trend'].capitalize())
                            st.write("**Trend Strength:**", trends['trend_strength'].capitalize())
                            if trends['price_change_percent'] != 0:
                                st.write("**Price Change:**", f"{trends['price_change_percent']}%")

                        with col_trend2:
                            if trends['indicators']['rsi'] is not None:
                                st.write("**RSI:**", trends['indicators']['rsi'])
                            if trends['support_resistance']['support'] is not None:
                                st.write("**Support Level:**", trends['support_resistance']['support'])
                            if trends['support_resistance']['resistance'] is not None:
                                st.write("**Resistance Level:**", trends['support_resistance']['resistance'])

                        st.write("**Analysis:**", trends['analysis'])
                    else:
                        st.error("Unable to fetch price data. The CoinGecko public API may be experiencing issues. Please try again in a few minutes.")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    with col2:
        st.subheader("News & Sentiment")
        news_placeholder = st.empty()
        sentiment = {'overall': 'No news data available'}  # Initialize sentiment
        news = []  # Initialize news

        with st.spinner('Fetching news...'):
            if not os.environ.get('NEWS_API_KEY'):
                news_placeholder.warning("NewsAPI key is missing. Please add your NewsAPI key to fetch news data.")
            else:
                try:
                    news = get_crypto_news(crypto)
                    if news:
                        sentiment = analyze_sentiment(news)
                        st.markdown("### Latest News")
                        for item in news[:5]:
                            with st.expander(item['title']):
                                st.markdown(f"_{item['summary']}_")
                                sentiment_color = (
                                    "🟢" if item['sentiment'] == 'positive'
                                    else "🔴" if item['sentiment'] == 'negative'
                                    else "⚪"
                                )
                                st.markdown(f"Sentiment: {sentiment_color} {item['sentiment']}")
                    else:
                        news_placeholder.warning("No recent news found for this cryptocurrency.")
                except Exception as e:
                    st.error(f"Error fetching news: {str(e)}")

    # Social Media Analysis
    st.subheader("Social Media Insights")
    social_placeholder = st.empty()

    # Check for Reddit credentials
    if not (os.environ.get('REDDIT_CLIENT_ID') and os.environ.get('REDDIT_CLIENT_SECRET')):
        social_placeholder.warning("Reddit API credentials are missing. Please add your Reddit Client ID and Secret to enable social media analysis.")
        social_data = {'reddit': pd.DataFrame(), 'twitter': pd.DataFrame()}  # Initialize empty social data
    else:
        social_data = get_social_data(crypto)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("### Reddit Sentiment")
        if not social_data['reddit'].empty:
            reddit_sentiment = social_data['reddit']
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=['Positive', 'Neutral', 'Negative'],
                y=[
                    len(reddit_sentiment[reddit_sentiment['sentiment'] > 0.05]),
                    len(reddit_sentiment[(reddit_sentiment['sentiment'] >= -0.05) & (reddit_sentiment['sentiment'] <= 0.05)]),
                    len(reddit_sentiment[reddit_sentiment['sentiment'] < -0.05])
                ]
            ))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No Reddit data available.")

    with col4:
        st.markdown("### Twitter Sentiment")
        if not social_data['twitter'].empty:
            twitter_sentiment = social_data['twitter']
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=['Positive', 'Neutral', 'Negative'],
                y=[
                    len(twitter_sentiment[twitter_sentiment['sentiment'] > 0.05]),
                    len(twitter_sentiment[(twitter_sentiment['sentiment'] >= -0.05) & (twitter_sentiment['sentiment'] <= 0.05)]),
                    len(twitter_sentiment[twitter_sentiment['sentiment'] < -0.05])
                ]
            ))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No Twitter data available.")

    # Chat Interface
    st.subheader("Chat with Assistant")

    # Initialize session state for chat input if not exists
    if 'chat_input' not in st.session_state:
        st.session_state.chat_input = ""

    # Chat input with key for proper state management
    user_question = st.text_input(
        "Ask me anything about the current crypto market:",
        key="chat_input",
        on_change=lambda: setattr(st.session_state, 'chat_input', "")
    )

    if user_question:
        response = "Based on the current analysis:\n\n"
        if trends is not None:
            response += f"📈 {crypto} Price Analysis:\n"
            response += f"• Current trend: {trends['trend'].capitalize()}\n"
            response += f"• {trends['analysis']}\n\n"

        if news:
            response += "📰 News Sentiment:\n"
            response += f"• Overall sentiment: {sentiment['overall']}\n"
            recent_news = news[:3]
            response += "• Recent headlines:\n"
            for item in recent_news:
                response += f"  - {item['title']} ({item['sentiment']})\n"

        st.write(response)

    # Generate and store daily report
    if st.button("Generate Daily Report"):
        with st.spinner('Generating report...'):
            try:
                report_data = {
                    'timestamp': datetime.now().isoformat(),
                    'crypto': crypto,
                    'price_analysis': {
                        'trend': trends.get('trend', 'N/A'),
                        'strength': trends.get('trend_strength', 'N/A'),
                        'analysis': trends.get('analysis', 'N/A'),
                        'indicators': trends.get('indicators', {})
                    },
                    'news_sentiment': sentiment.get('overall', 'No news data available'),
                    'social_data': {
                        'reddit': social_data.get('reddit', pd.DataFrame()).to_dict('records') if not social_data.get('reddit', pd.DataFrame()).empty else [],
                        'twitter': social_data.get('twitter', pd.DataFrame()).to_dict('records') if not social_data.get('twitter', pd.DataFrame()).empty else []
                    }
                }

                store_analysis_results(report_data)
                send_daily_report(report_data)
                st.success("Daily report generated and sent!")
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")
                print(f"Report generation error: {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.info("Please try refreshing the page. If the error persists, contact support.")