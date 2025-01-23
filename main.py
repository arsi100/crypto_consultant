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

# Helper function for JSON serialization
def json_serial(obj):
    if isinstance(obj, (datetime, pd.Timestamp)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def generate_daily_report(crypto, trends, news, sentiment):
    """
    Separate function to handle report generation logic
    Returns (success, message) tuple
    """
    try:
        if not trends:
            return False, "No price analysis data available. Please wait for data to load."

        # Prepare report data
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

        # Serialize data
        try:
            serialized_data = json.loads(json.dumps(report_data, default=json_serial))
        except Exception as e:
            logger.error(f"Error serializing report data: {str(e)}")
            return False, "Error processing report data. Please try again."

        # Store results
        try:
            store_analysis_results(serialized_data)
        except Exception as e:
            logger.warning(f"Could not store analysis results: {str(e)}")
            # Continue even if storage fails

        # Send report
        try:
            send_daily_report(serialized_data)
        except Exception as e:
            logger.error(f"Error sending report: {str(e)}")
            return False, f"Error sending report: {str(e)}"

        return True, "Daily report generated and sent successfully!"

    except Exception as e:
        logger.error(f"Error in report generation: {str(e)}", exc_info=True)
        return False, f"Error generating report: {str(e)}"

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
            'x_cg_demo_api_key': api_key
        }

        headers = {
            'X-Cg-Api-Key': api_key,
            'User-Agent': 'CryptoIntelligence/1.0'
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return data[coin_id]['usd']
        else:
            logger.error(f"CoinGecko API error: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error fetching real-time price: {str(e)}")
        return None

from data_collectors.price_collector import get_crypto_prices, CoinGeckoClient # Assuming CoinGeckoClient is defined here
from data_collectors.news_collector import get_crypto_news
from data_collectors.social_collector import get_social_data
from analysis.price_analyzer import analyze_price_trends
from analysis.sentiment_analyzer import analyze_sentiment
from utils.email_sender import send_daily_report
from utils.data_storage import store_analysis_results

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
    st.session_state.selected_coin = None


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
        st.set_page_config(
            page_title="🤖 AI Crypto Research Assistant",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Sidebar with improved layout
        with st.sidebar:
            st.title("📊 Controls")

            # Coin selection with symbols and names
            coin_options = {f"{symbol} - {info['name']}": symbol 
                          for symbol, info in AVAILABLE_COINS.items()}

            selected_display = st.selectbox(
                "Select Cryptocurrency",
                options=list(coin_options.keys()),
                index=0 if st.session_state.selected_coin is None else 
                      list(coin_options.keys()).index(f"{st.session_state.selected_coin} - {AVAILABLE_COINS[st.session_state.selected_coin]['name']}")
            )

            # Extract symbol from display name
            crypto = coin_options[selected_display]
            st.session_state.selected_coin = crypto

            timeframe = st.selectbox(
                "Select Timeframe",
                ["24h", "7d", "30d"],
                index=0
            )

        # Main content area with responsive layout
        st.title("🤖 AI Crypto Research Assistant")

        # Get real-time price with error handling
        current_price = get_real_crypto_price(crypto)

        # Create three columns for better organization
        col1, col2, col3 = st.columns([2, 1, 2])

        with col1:
            st.subheader("Price Analysis")

            # Current Price Display
            if current_price:
                st.markdown(f"""
                <div style='padding: 1rem; background-color: #1E1E1E; border-radius: 10px; margin-bottom: 1rem;'>
                    <h2 style='margin: 0; color: #E0E0E0;'>{crypto} Current Price</h2>
                    <h1 style='margin: 0.5rem 0; color: #00FF00;'>${current_price:,.2f}</h1>
                    <p style='margin: 0; color: #808080; font-size: 0.8rem;'>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Unable to fetch current price. Using historical data only.")

        with col2:
            st.subheader("Trading Signal")
            if st.session_state.trends:
                signal_color = (
                    "🟢" if st.session_state.trends['trend'] == 'bullish'
                    else "🔴" if st.session_state.trends['trend'] == 'bearish'
                    else "⚪"
                )
                signal_text = (
                    "Strong Buy" if st.session_state.trends['trend'] == 'bullish' and st.session_state.trends['trend_strength'] == 'strong'
                    else "Buy" if st.session_state.trends['trend'] == 'bullish'
                    else "Strong Sell" if st.session_state.trends['trend'] == 'bearish' and st.session_state.trends['trend_strength'] == 'strong'
                    else "Sell" if st.session_state.trends['trend'] == 'bearish'
                    else "Hold"
                )
                st.markdown(f"""
                <div style='padding: 1rem; background-color: #1E1E1E; border-radius: 10px;'>
                    <h2 style='margin: 0.5rem 0;'>{signal_color} {signal_text}</h2>
                    <p style='color: #CCCCCC; font-size: 0.9em;'>Based on technical analysis</p>
                </div>
                """, unsafe_allow_html=True)

        with col3:
            st.subheader("Market Overview")
            if st.session_state.trends:
                st.metric(
                    "24h Change",
                    f"{st.session_state.trends['price_change_percent']:+.2f}%",
                    delta_color="normal"
                )

        # Technical Analysis section
        st.markdown("### 📊 Technical Analysis")

        try:
            prices = get_crypto_prices(crypto, timeframe)
            if prices is not None and not prices.empty:
                # Create price chart
                fig = go.Figure()

                # Add candlestick chart
                fig.add_trace(go.Candlestick(
                    x=prices['timestamp'],
                    open=prices['open'],
                    high=prices['high'],
                    low=prices['low'],
                    close=prices['close'],
                    name="Price"
                ))

                # Update layout for better readability
                fig.update_layout(
                    title=f"{crypto} Price Chart ({timeframe})",
                    yaxis_title="Price (USD)",
                    xaxis_title="Time",
                    template="plotly_dark",
                    height=600,  # Fixed height
                    margin=dict(l=50, r=50, t=50, b=50),  # Adjusted margins
                    showlegend=True,
                    yaxis=dict(side="right"),  # Move price axis to right side
                    xaxis=dict(rangeslider=dict(visible=False))  # Remove range slider
                )

                st.plotly_chart(fig, use_container_width=True)

                # Show technical indicators in an expander
                with st.expander("🔍 Technical Indicators", expanded=True):
                    st.markdown("""
                    ### Key Indicators Explained
                    - **RSI (Relative Strength Index)**: Measures momentum
                    - **Bollinger Bands**: Track price volatility
                    - **Support/Resistance**: Key price levels
                    """)

            else:
                st.error("Unable to load price data. Please try again later.")

        except Exception as e:
            logger.error(f"Error in price analysis: {str(e)}")
            st.error("Error analyzing price data. Please try again.")

        # Daily Report Section
        st.markdown("### 📈 Daily Report Generation")
        col_report1, col_report2 = st.columns([3, 1])

        with col_report1:
            st.markdown("""
            The daily report includes:
            - Price analysis and trends
            - Technical indicator summary
            - Market sentiment analysis
            - News impact assessment
            """)

        with col_report2:
            if st.button("Generate Daily Report", key="generate_report"):
                try:
                    with st.spinner("Generating report..."):
                        time.sleep(1)  # Simulate processing
                        st.success("Report generated successfully!")
                        st.download_button(
                            "Download Report",
                            data="Sample report content",  # Replace with actual report
                            file_name=f"crypto_report_{datetime.now().strftime('%Y%m%d')}.txt",
                            mime="text/plain"
                        )
                except Exception as e:
                    st.error(f"Error generating report: {str(e)}")

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
            # Create placeholders for progress tracking
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            success_placeholder = st.empty()

            try:
                with progress_placeholder.container():
                    progress_bar = st.progress(0)

                    # Step 1: Validation (25%)
                    status_placeholder.text("Validating data...")
                    progress_bar.progress(25)
                    time.sleep(0.5)  # Small delay for visual feedback

                    # Step 2: Generate Report (50%)
                    status_placeholder.text("Generating report...")
                    progress_bar.progress(50)

                    # Call report generation function
                    success, message = generate_daily_report(
                        crypto,
                        st.session_state.trends,
                        st.session_state.news,
                        st.session_state.sentiment
                    )

                    # Step 3: Process Result (100%)
                    progress_bar.progress(100)
                    time.sleep(0.5)  # Small delay for visual feedback

                    # Clear progress indicators
                    progress_placeholder.empty()
                    status_placeholder.empty()

                    # Show final status
                    if success:
                        success_placeholder.success(message)
                    else:
                        success_placeholder.error(message)
                        st.info("Please check your connection and try again. If the issue persists, contact support.")

            except Exception as e:
                # Ensure UI elements are cleaned up
                progress_placeholder.empty()
                status_placeholder.empty()
                success_placeholder.error(f"Unexpected error: {str(e)}")
                st.info("Please try again. If the issue persists, contact support.")
                logger.error(f"Unexpected error in report generation UI: {str(e)}", exc_info=True)

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