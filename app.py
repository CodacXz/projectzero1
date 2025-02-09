import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import os

# Configure page
st.set_page_config(
    page_title="Saudi Stock Analysis",
    page_icon="📈",
    layout="wide"
)

# Constants
MARKETAUX_API_KEY = os.getenv('MARKETAUX_API_KEY')
MARKETAUX_BASE_URL = "https://api.marketaux.com/v1/news/all"

def get_news_sentiment(symbol):
    """Fetch news sentiment for a given stock symbol"""
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
        
        return avg_sentiment, news_items
        
    except Exception as e:
        st.error(f"Error fetching sentiment data: {str(e)}")
        return None, []

def main():
    # Sidebar
    st.sidebar.title("Settings")
    symbol = st.sidebar.text_input("Enter Stock Symbol (e.g., 2222):", value="2222")
    if not symbol.endswith('.SR'):
        symbol = f"{symbol}.SR"
    
    # Fetch company info
    try:
        ticker = yf.Ticker(symbol)
        company_name = ticker.info.get('longName', 'Unknown Company')
        st.sidebar.markdown(f"**Company:** {company_name}")
    except:
        st.sidebar.warning("Could not fetch company information")

    # Main content
    st.title("📰 Saudi Stock Market Analysis")
    
    # Section 1: Sentiment Analysis
    st.header("Sentiment Analysis & News")
    
    sentiment_score, news_items = get_news_sentiment(symbol)
    
    if sentiment_score is not None:
        # Create three columns
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
        
        with col2:
            st.subheader("Interpretation")
            if sentiment_score > 0.3:
                st.success("Very Positive")
            elif sentiment_score > 0.1:
                st.success("Positive")
            elif sentiment_score > -0.1:
                st.info("Neutral")
            elif sentiment_score > -0.3:
                st.error("Negative")
            else:
                st.error("Very Negative")
        
        with col3:
            st.subheader("Market Impact")
            impact = "High" if abs(sentiment_score) > 0.3 else "Medium" if abs(sentiment_score) > 0.1 else "Low"
            st.metric("Potential Impact", impact)
    
        # News Display
        st.subheader("Latest News Analysis")
        for idx, news in enumerate(news_items):
            with st.expander(f"{news['title']} ({news['published_at'][:10]})"):
                sentiment_emoji = "🟢" if news['sentiment'] > 0.1 else "🔴" if news['sentiment'] < -0.1 else "⚪"
                st.markdown(f"""
                **Sentiment Score:** {sentiment_emoji} {news['sentiment']:.2f}  
                **Description:** {news['description']}  
                **Source:** [Read more]({news['url']})
                """)
                
                # Extract keywords/entities
                if news['keywords']:
                    keywords = [entity.get('name', '') for entity in news['keywords'] if entity.get('name')]
                    st.markdown("**Keywords:** " + ", ".join(keywords))
    
    else:
        st.warning("No recent news data available for this stock.")
    
    # Section 2: Technical Analysis based on News
    st.markdown("---")
    st.header("Technical Analysis Based on News")
    
    if news_items:
        # Create analysis based on news sentiment
        positive_news = sum(1 for news in news_items if news['sentiment'] > 0.1)
        negative_news = sum(1 for news in news_items if news['sentiment'] < -0.1)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("News Sentiment Distribution")
            sentiment_data = {
                'Positive': positive_news,
                'Neutral': len(news_items) - positive_news - negative_news,
                'Negative': negative_news
            }
            st.bar_chart(sentiment_data)
        
        with col2:
            st.subheader("Trading Signals")
            if sentiment_score > 0.2:
                st.success("🔥 Strong Buy Signal")
            elif sentiment_score > 0:
                st.success("📈 Buy Signal")
            elif sentiment_score < -0.2:
                st.error("💥 Strong Sell Signal")
            elif sentiment_score < 0:
                st.error("📉 Sell Signal")
            else:
                st.info("⚖️ Hold/Neutral Signal")
    
    # Footer
    st.markdown("---")
    st.caption("Data provided by MarketAux API")

if __name__ == "__main__":
    main()
