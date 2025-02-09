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
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.getenv('MARKETAUX_API_KEY', '')

# Constants
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
    if not st.session_state.api_key:
        st.error("Please enter your MarketAux API key in the sidebar.")
        return 0, []

    current_time = time.time()
    
    # Check cache first
    if not force_refresh and symbol in st.session_state.news_cache:
        cached_data = st.session_state.news_cache[symbol]
        if current_time - cached_data['timestamp'] < NEWS_CACHE_DURATION:
            return cached_data['sentiment'], cached_data['news']
    
    try:
        # Fetch news data
        params = {
            'symbols': symbol,
            'filter_entities': True,
            'language': 'en',
            'api_token': st.session_state.api_key
        }
        
        response = requests.get(MARKETAUX_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        news_items = data.get('data', [])
        sentiment_score = sum(float(news.get('sentiment', 0)) for news in news_items) / len(news_items) if news_items else 0
        
        # Update cache
        st.session_state.news_cache[symbol] = {
            'timestamp': current_time,
            'sentiment': sentiment_score,
            'news': news_items
        }
        st.session_state.last_fetch_time = current_time
        
        return sentiment_score, news_items
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            st.error("Invalid API key. Please check your MarketAux API key in the sidebar.")
        else:
            st.error(f"Error fetching news data: {str(e)}")
        return 0, []
    except Exception as e:
        st.error(f"Error fetching news data: {str(e)}")
        return 0, []

def main():
    # Sidebar
    st.sidebar.title("Settings")
    
    # API Key input
    st.sidebar.markdown("### API Settings")
    api_key = st.sidebar.text_input(
        "MarketAux API Key",
        value=st.session_state.api_key,
        type="password",
        help="Enter your MarketAux API key. Get one at https://www.marketaux.com/"
    )
    
    # Update API key in session state
    if api_key != st.session_state.api_key:
        st.session_state.api_key = api_key
        st.session_state.news_cache = {}  # Clear cache when API key changes
    
    st.sidebar.markdown("---")
    
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
    
    if not st.session_state.api_key:
        st.warning("⚠️ Please enter your MarketAux API key in the sidebar to fetch news data.")
        st.stop()
    
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
        # Display sentiment score
        st.metric("Overall Sentiment Score", f"{sentiment_score:.2f}")
        
        # Display news items
        if news_items:
            for news in news_items:
                with st.expander(news.get('title', 'No Title')):
                    st.write(f"**Published:** {news.get('published_at', 'Unknown date')}")
                    st.write(f"**Sentiment:** {float(news.get('sentiment', 0)):.2f}")
                    st.write(news.get('description', 'No description available'))
                    if news.get('url'):
                        st.markdown(f"[Read more]({news['url']})")
        else:
            st.info("No news items found for this stock.")

if __name__ == "__main__":
    main()
