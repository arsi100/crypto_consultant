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

# Helper function for JSON serialization (from original code)
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

from data_collectors.price_collector import get_crypto_prices # Assuming this is defined elsewhere
from data_collectors.news_collector import get_crypto_news # Assuming this is defined elsewhere
from data_collectors.social_collector import get_social_data # Assuming this is defined elsewhere
from analysis.price_analyzer import analyze_price_trends # Assuming this is defined elsewhere
from analysis.sentiment_analyzer import analyze_sentiment # Assuming this is defined elsewhere
from utils.email_sender import send_daily_report # Assuming this is defined elsewhere
from utils.data_storage import store_analysis_results # Assuming this is defined elsewhere


# Initialize session state
if 'page_loaded' not in st.session_state:
    st.session_state.page_loaded = False
    st.session_state.current_coin = None
    st.session_state.error_state = None
    st.session_state.report_generating = False

def handle_error(error_msg: str):
    """Centralized error handling"""
    logger.error(error_msg)
    st.session_state.error_state = error_msg
    st.error(error_msg)

def reset_error_state():
    """Reset error state"""
    st.session_state.error_state = None

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


def main():
    try:
        # Page configuration
        st.set_page_config(
            page_title="CryptoAI Research Platform",
            layout="wide",
            initial_sidebar_state="expanded",
            page_icon="📈"
        )

        # Apply custom CSS
        st.markdown("""
        <style>
        .main {
            padding: 0rem 1rem;
        }
        .stButton>button {
            width: 100%;
        }
        .reportbox {
            background-color: #262730;
            padding: 1rem;
            border-radius: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)

        # Sidebar
        with st.sidebar:
            st.title("📊 Controls")

            # Coin selection
            coin_options = {f"{symbol} - {info['name']}": symbol 
                          for symbol, info in AVAILABLE_COINS.items()}

            selected_display = st.selectbox(
                "Select Cryptocurrency",
                options=list(coin_options.keys())
            )

            # Extract symbol and handle coin change
            new_coin = coin_options[selected_display]
            if st.session_state.current_coin != new_coin:
                st.session_state.current_coin = new_coin
                reset_error_state()

            # Timeframe selection
            timeframe = st.selectbox(
                "Timeframe",
                ["24h", "7d", "30d"]
            )

        # Main content
        st.title("CryptoAI Research Platform")

        # Only proceed if we have a selected coin
        if not st.session_state.current_coin:
            st.info("Please select a cryptocurrency to begin analysis")
            return

        try:
            # Get current price
            current_price = get_real_crypto_price(st.session_state.current_coin)

            # Layout
            price_col, signal_col, chart_col = st.columns([1, 1, 2])

            with price_col:
                display_price_info(current_price, st.session_state.current_coin)

            with signal_col:
                display_trading_signal()

            with chart_col:
                display_price_chart(st.session_state.current_coin, timeframe)

            # Technical Analysis Section
            st.markdown("---")
            tech_col1, tech_col2 = st.columns(2)

            with tech_col1:
                display_technical_indicators()

            with tech_col2:
                if st.button("Generate Analysis Report", use_container_width=True):
                    generate_and_display_report()

        except Exception as e:
            handle_error(f"Error analyzing data: {str(e)}")

    except Exception as e:
        handle_error(f"Application error: {str(e)}")

def display_price_info(price, coin):
    """Display current price information"""
    if price:
        st.metric(
            label=f"{coin} Price",
            value=f"${price:,.2f}",
            delta=None  # Add price change here
        )
    else:
        st.error("Unable to fetch current price")

def display_trading_signal():
    """Display trading signal and strength"""
    # Placeholder -  Add trading signal logic here using st.session_state.trends if available.
    st.write("Trading signal display will be implemented here.")
    pass


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
        handle_error(f"Error displaying chart: {str(e)}")

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

def display_technical_indicators():
    """Display technical indicators"""
    st.write("Technical indicator display will be implemented here.")
    pass


def generate_and_display_report():
    """Generate and display analysis report"""
    try:
        if st.session_state.report_generating:
            return

        st.session_state.report_generating = True

        with st.spinner("Generating comprehensive analysis report..."):
            # Add report generation logic here
            time.sleep(2)  # Simulate processing

            report_data = {
                "timestamp": datetime.now().isoformat(),
                "analysis": "Sample analysis"
            }

            # Create download button
            st.download_button(
                "Download Report",
                data=json.dumps(report_data, indent=2),
                file_name=f"crypto_report_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )

        st.success("Report generated successfully!")

    except Exception as e:
        handle_error(f"Error generating report: {str(e)}")
    finally:
        st.session_state.report_generating = False


if __name__ == "__main__":
    main()