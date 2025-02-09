import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import os
import time

# Configure page
st.set_page_config(
    page_title="Saudi Stock Analysis",
    layout="wide"
)

# Initialize session state
if 'news_cache' not in st.session_state:
    st.session_state.news_cache = {}
if 'last_fetch_time' not in st.session_state:
    st.session_state.last_fetch_time = None
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True

# Constants
MARKETAUX_API_KEY = os.getenv('MARKETAUX_API_KEY')
MARKETAUX_BASE_URL = "https://api.marketaux.com/v1/news/all"
REFRESH_INTERVAL = 300  # 5 minutes in seconds
NEWS_CACHE_DURATION = 300  # 5 minutes in seconds

def format_symbol(symbol):
    """Format the stock symbol correctly for Saudi stocks"""
    # Remove any existing .SR suffix
    symbol = symbol.replace('.SR', '').strip()
    
    # Pad with zeros if needed (Saudi stocks are 4 digits)
    symbol = symbol.zfill(4)
    
    # Add .SR suffix
    return f"{symbol}.SR"

def get_stock_info(symbol):
    """Fetch stock information with error handling"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Check if we got valid data
        if not info or 'longName' not in info:
            return {
                'name': f"Stock {symbol}",
                'sector': 'Unknown',
                'currency': 'SAR'
            }
            
        return {
            'name': info.get('longName', f"Stock {symbol}"),
            'sector': info.get('sector', 'Unknown'),
            'currency': info.get('currency', 'SAR')
        }
    except Exception as e:
        st.sidebar.error(f"Error fetching stock data: {str(e)}")
        return {
            'name': f"Stock {symbol}",
            'sector': 'Unknown',
            'currency': 'SAR'
        }

def get_news_sentiment(symbol, force_refresh=False):
    """Fetch news sentiment with caching"""
    # ... existing code ...

def main():
    # Sidebar
    st.sidebar.title("Settings")
    
    # Stock symbol input with validation
    raw_symbol = st.sidebar.text_input("Enter Stock Symbol (e.g., 2222):", value="2222")
    symbol = format_symbol(raw_symbol)
    
    # Display formatted symbol
    st.sidebar.caption(f"Formatted Symbol: {symbol}")
    
    # Fetch and display stock info
    stock_info = get_stock_info(symbol)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    **Company:** {stock_info['name']}  
    **Sector:** {stock_info['sector']}  
    **Currency:** {stock_info['currency']}
    """)
    
    # Auto-refresh toggle
    st.sidebar.markdown("---")
    st.session_state.auto_refresh = st.sidebar.checkbox("Enable Auto-refresh", value=st.session_state.auto_refresh)
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        sentiment_score, news_items = get_news_sentiment(symbol, force_refresh=True)
        st.rerun()
    
    # Show last fetch time
    if st.session_state.last_fetch_time:
        time_diff = time.time() - st.session_state.last_fetch_time
        if time_diff < 60:
            time_str = f"{int(time_diff)} seconds ago"
        else:
            time_str = f"{int(time_diff/60)} minutes ago"
        st.sidebar.caption(f"Last updated: {time_str}")

    # Main content
    st.title("📰 Saudi Stock Analysis")
    st.subheader(f"Analysis for {stock_info['name']} ({symbol})")
    
    # Auto-refresh logic
    if st.session_state.auto_refresh:
        if (st.session_state.last_fetch_time is None or 
            time.time() - st.session_state.last_fetch_time >= REFRESH_INTERVAL):
            sentiment_score, news_items = get_news_sentiment(symbol)
            st.rerun()
    
    # Get cached data or fetch new data
    sentiment_score, news_items = get_news_sentiment(symbol)
    
    # Create a container for real-time updates
    main_container = st.container()
    
    with main_container:
        # ... rest of your existing display code ...

if __name__ == "__main__":
    main()
