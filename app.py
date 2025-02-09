import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import os
import time
from collections import deque

# Configure page
st.set_page_config(
    page_title="Saudi Stock Analysis",
    layout="wide"
)

# Initialize session state for news cache
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

def get_news_sentiment(symbol, force_refresh=False):
    """Fetch news sentiment with caching"""
    current_time = time.time()
    
    # Check cache first
    if not force_refresh and symbol in st.session_state.news_cache:
        cache_time, cache_data = st.session_state.news_cache[symbol]
        if current_time - cache_time < NEWS_CACHE_DURATION:
            return cache_data

    try:
        clean_symbol = symbol.replace('.SR', '')
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        params = {
            'api_token': MARKETAUX_API_KEY,
            'symbols': clean_symbol,
            'filter_entities': True,
            'language': 'en',
            'countries': 'sa',
            'limit': 10,
            'published_after': start_date.strftime('%Y-%m-%d'),
            'published_before': end_date.strftime('%Y-%m-%d')
        }
        
        response = requests.get(MARKETAUX_BASE_URL, params=params)
        data = response.json()
        
        if 'data' not in data or not data['data']:
            return None, []
            
        sentiments = [article['entities'][0]['sentiment_score'] 
                     for article in data['data'] 
                     if 'entities' in article and article['entities']]
        
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        news_items = [{
            'title': article['title'],
            'sentiment': article['entities'][0]['sentiment_score'] if article['entities'] else 0,
            'url': article['url'],
            'published_at': article['published_at'],
            'description': article.get('description', ''),
            'keywords': article.get('entities', [])
        } for article in data['data']]
        
        result = (avg_sentiment, news_items)
        
        # Update cache
        st.session_state.news_cache[symbol] = (current_time, result)
        st.session_state.last_fetch_time = current_time
        
        return result
        
    except Exception as e:
        st.error(f"Error fetching sentiment data: {str(e)}")
        return None, []

def main():
    # Sidebar
    st.sidebar.title("Settings")
    symbol = st.sidebar.text_input("Enter Stock Symbol (e.g., 2222):", value="2222")
    if not symbol.endswith('.SR'):
        symbol = f"{symbol}.SR"
    
    # Auto-refresh toggle
    st.sidebar.markdown("---")
    st.session_state.auto_refresh = st.sidebar.checkbox("Enable Auto-refresh", value=st.session_state.auto_refresh)
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        sentiment_score, news_items = get_news_sentiment(symbol, force_refresh=True)
        st.rerun()  # Updated from experimental_rerun()
    
    # Show last fetch time
    if st.session_state.last_fetch_time:
        time_diff = time.time() - st.session_state.last_fetch_time
        if time_diff < 60:
            time_str = f"{int(time_diff)} seconds ago"
        else:
            time_str = f"{int(time_diff/60)} minutes ago"
        st.sidebar.caption(f"Last updated: {time_str}")
    
    # Fetch company info
    try:
        ticker = yf.Ticker(symbol)
        company_name = ticker.info.get('longName', 'Unknown Company')
        st.sidebar.markdown(f"**Company:** {company_name}")
    except:
        st.sidebar.warning("Could not fetch company information")

    # Main content
    st.title("📰 Saudi Stock Market Analysis")
    
    # Auto-refresh logic
    if st.session_state.auto_refresh:
        if (st.session_state.last_fetch_time is None or 
            time.time() - st.session_state.last_fetch_time >= REFRESH_INTERVAL):
            sentiment_score, news_items = get_news_sentiment(symbol)
            st.rerun()  # Updated from experimental_rerun()
    
    # Get cached data or fetch new data
    sentiment_score, news_items = get_news_sentiment(symbol)
    
    # Create a container for real-time updates
    main_container = st.container()
    
    with main_container:
        st.header("Sentiment Analysis & News")
        
        if sentiment_score is not None:
            # Display sentiment analysis
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.subheader("Overall Market Sentiment")
                sentiment_color = 'green' if sentiment_score > 0.1 else 'red' if sentiment_score < -0.1 else 'gray'
                st.markdown(f"""
                <div style='text-align: center; padding: 20px; background-color: rgba(0,0,0,0.1); border-radius: 10px;'>
                    <h1 style='color: {sentiment_color}'>{sentiment_score:.2f}</h1>
                    <p>Sentiment Score</p>
                </div>
                """, unsafe_allow_html=True)
            
            # News Display with "New" badge for recent news
            st.subheader("Latest News Analysis")
            for idx, news in enumerate(news_items):
                news_time = datetime.strptime(news['published_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
                is_new = (datetime.utcnow() - news_time) < timedelta(hours=1)
                
                title_prefix = "🆕 " if is_new else ""
                with st.expander(f"{title_prefix}{news['title']} ({news['published_at'][:10]})"):
                    sentiment_emoji = "🟢" if news['sentiment'] > 0.1 else "🔴" if news['sentiment'] < -0.1 else "⚪"
                    st.markdown(f"""
                    **Sentiment Score:** {sentiment_emoji} {news['sentiment']:.2f}  
                    **Description:** {news['description']}  
                    **Source:** [Read more]({news['url']})
                    """)
                    
                    if news['keywords']:
                        keywords = [entity.get('name', '') for entity in news['keywords'] if entity.get('name')]
                        st.markdown("**Keywords:** " + ", ".join(keywords))
        
        else:
            st.warning("No recent news data available for this stock.")

    # Footer with auto-refresh status
    st.markdown("---")
    if st.session_state.auto_refresh:
        next_refresh = REFRESH_INTERVAL - (time.time() - st.session_state.last_fetch_time) if st.session_state.last_fetch_time else 0
        st.caption(f"Auto-refresh enabled (Next refresh in {int(next_refresh)} seconds)")
    st.caption("Data provided by MarketAux API")

if __name__ == "__main__":
    main()
