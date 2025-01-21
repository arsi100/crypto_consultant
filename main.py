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
            st.plotly_chart(fig, use_container_width=True)

            # Show trend analysis
            trends = analyze_price_trends(prices)
            st.markdown("### Trend Analysis")
            st.write(trends)
        else:
            st.error("Unable to fetch price data. Please try again later.")

    with col2:
        st.subheader("News & Sentiment")
        news = get_crypto_news(crypto)

        if news:
            sentiment = analyze_sentiment(news)

            st.markdown("### Latest News")
            for item in news[:5]:
                st.markdown(f"**{item['title']}**")
                st.markdown(f"_{item['summary']}_")
                sentiment_color = (
                    "🟢" if item['sentiment'] == 'positive' 
                    else "🔴" if item['sentiment'] == 'negative' 
                    else "⚪"
                )
                st.markdown(f"Sentiment: {sentiment_color} {item['sentiment']}")
                st.markdown("---")
        else:
            st.warning("No recent news found for this cryptocurrency.")

    # Social Media Analysis
    st.subheader("Social Media Insights")
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
    user_question = st.text_input("Ask me anything about the current crypto market:")
    if user_question:
        response = f"Based on the current analysis:\n\n"
        if not prices.empty:
            response += f"• {crypto} is showing a {trends['trend']} trend\n"
        if news:
            response += f"• Overall sentiment from news is {sentiment['overall']}\n"
        if not social_data['reddit'].empty or not social_data['twitter'].empty:
            response += f"• Social media sentiment is showing significant activity\n"
        st.write(response)

    # Generate and store daily report
    if st.button("Generate Daily Report"):
        report_data = {
            'crypto': crypto,
            'price_analysis': trends if not prices.empty else {},
            'sentiment': sentiment if news else {},
            'social_data': social_data
        }
        store_analysis_results(report_data)
        send_daily_report(report_data)
        st.success("Daily report generated and sent!")

if __name__ == "__main__":
    main()