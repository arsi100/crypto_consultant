import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import os
import time
import json

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

            # Add more detailed technical analysis
            if trends['indicators']['rsi'] is not None:
                rsi_val = trends['indicators']['rsi']
                response += f"• RSI Analysis: {rsi_val:.1f} - "
                if rsi_val > 70:
                    response += "Market is overbought, potential reversal incoming\n"
                elif rsi_val < 30:
                    response += "Market is oversold, watch for potential upward movement\n"
                else:
                    response += "RSI in neutral territory\n"

            if all(v is not None for v in [trends['indicators']['macd'], trends['indicators']['macd_signal']]):
                macd_diff = trends['indicators']['macd'] - trends['indicators']['macd_signal']
                response += f"• MACD Signal: {'Bullish' if macd_diff > 0 else 'Bearish'} momentum "
                response += f"(Difference: {macd_diff:.4f})\n"

        if news:
            response += "\n📰 News Sentiment:\n"
            response += f"• Overall market sentiment: {sentiment['overall'].capitalize()}\n"
            response += "• Key news impacts:\n"
            for item in news[:3]:
                response += f"  - {item['title']}\n"
                response += f"    Sentiment: {item['sentiment'].capitalize()}\n"
                if 'summary' in item:
                    response += f"    {item['summary'][:150]}...\n"

            # Add social media context
            if isinstance(social_data, dict):
                response += "\n📱 Social Media Insights:\n"
                for platform in ['reddit', 'twitter']:
                    if platform in social_data and not social_data[platform].empty:
                        df = social_data[platform]
                        positive = len(df[df['sentiment'] > 0.05])
                        negative = len(df[df['sentiment'] < -0.05])
                        total = len(df)
                        if total > 0:
                            response += f"• {platform.capitalize()} Sentiment:\n"
                            response += f"  - Positive: {positive/total*100:.1f}%\n"
                            response += f"  - Negative: {negative/total*100:.1f}%\n"
                            response += f"  - Neutral: {(total-positive-negative)/total*100:.1f}%\n"

        st.write(response)

    # Generate and store daily report
    if st.button("Generate Daily Report"):
        with st.spinner('Generating report...'):
            try:
                # Ensure we have valid data before generating report
                if not trends:
                    st.error("No price analysis data available. Please wait for data to load.")
                    return

                # Prepare report data with proper error handling
                report_data = {
                    'timestamp': datetime.now(),
                    'crypto': crypto,
                    'price_analysis': {
                        'trend': trends.get('trend', 'N/A'),
                        'strength': trends.get('trend_strength', 'N/A'),
                        'analysis': trends.get('analysis', 'N/A'),
                        'indicators': trends.get('indicators', {})
                    }
                }

                # Add sentiment data if available
                if isinstance(sentiment, dict) and 'overall' in sentiment:
                    report_data['news_sentiment'] = sentiment['overall']
                else:
                    report_data['news_sentiment'] = 'No news data available'

                # Process social data with proper error handling
                social_report = {'reddit': [], 'twitter': []}
                if isinstance(social_data, dict):
                    for platform in ['reddit', 'twitter']:
                        if platform in social_data and not social_data[platform].empty:
                            try:
                                platform_data = social_data[platform].copy()
                                # Convert timestamps to string format
                                if 'timestamp' in platform_data.columns:
                                    platform_data['timestamp'] = platform_data['timestamp'].apply(lambda x: x.isoformat() if pd.notnull(x) else None)
                                social_report[platform] = platform_data.to_dict('records')
                            except Exception as e:
                                print(f"Error processing {platform} data: {str(e)}")
                                social_report[platform] = []

                report_data['social_data'] = social_report

                # Store and send report with proper JSON serialization
                try:
                    store_analysis_results(json.loads(json.dumps(report_data, default=json_serial)))
                    send_daily_report(report_data)
                    st.success("Daily report generated and sent successfully!")
                except Exception as e:
                    st.error(f"Error saving/sending report: {str(e)}")
                    print(f"Report save/send error: {str(e)}")

            except Exception as e:
                st.error(f"Error generating report: {str(e)}")
                print(f"Report generation error: {str(e)}")

    # Previous chat interface code remains unchanged

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.info("Please try refreshing the page. If the error persists, contact support.")