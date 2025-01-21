import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

from data_collectors.price_collector import get_crypto_prices
from data_collectors.news_collector import get_crypto_news
from data_collectors.social_collector import get_social_data
from analysis.price_analyzer import analyze_price_trends
from analysis.sentiment_analyzer import analyze_sentiment
from utils.email_sender import send_daily_report
from utils.data_storage import store_analysis_results

st.set_page_config(page_title="Crypto Research Assistant", layout="wide")

def main():
    st.title("🤖 AI Crypto Research Assistant")
    
    # Sidebar
    st.sidebar.title("Controls")
    crypto = st.sidebar.selectbox(
        "Select Cryptocurrency",
        ["BTC", "ETH", "BNB", "XRP", "ADA"]
    )
    
    timeframe = st.sidebar.selectbox(
        "Select Timeframe",
        ["24h", "7d", "30d"]
    )

    # Main content area
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Price Analysis")
        prices = get_crypto_prices(crypto, timeframe)
        
        # Create price chart
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=prices['timestamp'],
            open=prices['open'],
            high=prices['high'],
            low=prices['low'],
            close=prices['close']
        ))
        st.plotly_chart(fig)

        # Show trend analysis
        trends = analyze_price_trends(prices)
        st.markdown("### Trend Analysis")
        st.write(trends)

    with col2:
        st.subheader("News & Sentiment")
        news = get_crypto_news(crypto)
        sentiment = analyze_sentiment(news)
        
        st.markdown("### Latest News")
        for item in news[:5]:
            st.markdown(f"**{item['title']}**")
            st.markdown(f"_{item['summary']}_")
            st.markdown(f"Sentiment: {item['sentiment']}")
            st.markdown("---")

    # Social Media Analysis
    st.subheader("Social Media Insights")
    social_data = get_social_data(crypto)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("### Reddit Sentiment")
        reddit_sentiment = pd.DataFrame(social_data['reddit'])
        st.bar_chart(reddit_sentiment['sentiment'])

    with col4:
        st.markdown("### Twitter Sentiment")
        twitter_sentiment = pd.DataFrame(social_data['twitter'])
        st.bar_chart(twitter_sentiment['sentiment'])

    # Chat Interface
    st.subheader("Chat with Assistant")
    user_question = st.text_input("Ask me anything about the current crypto market:")
    if user_question:
        # Simple response based on collected data
        st.write(f"Based on the current analysis, {crypto} is showing {trends['trend']} trend with {sentiment['overall']} sentiment from news and social media.")

    # Generate and store daily report
    if st.button("Generate Daily Report"):
        report_data = {
            'crypto': crypto,
            'price_analysis': trends,
            'sentiment': sentiment,
            'social_data': social_data
        }
        store_analysis_results(report_data)
        send_daily_report(report_data)
        st.success("Daily report generated and sent!")

if __name__ == "__main__":
    main()
