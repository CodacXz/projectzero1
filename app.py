def get_news_sentiment(symbol, force_refresh=False):
    """Fetch news sentiment with improved news extraction and prioritization"""
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
        # Enhanced parameters for better news extraction
        params = {
            'symbols': symbol,
            'filter_entities': True,
            'language': 'en',
            'api_token': st.session_state.api_key,
            'limit': 50,  # Increase limit to get more news
            'sort': 'published_at',  # Sort by publication date
            'countries': 'sa',  # Focus on Saudi Arabia
            'industries': 'finance,technology,energy',  # Add relevant industries
            'date_from': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),  # Last 30 days
            'entity_types': 'company,equity'  # Focus on company and equity news
        }
        
        response = requests.get(MARKETAUX_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        news_items = data.get('data', [])
        
        # Enhanced news processing and prioritization
        processed_news = []
        for news in news_items:
            # Calculate priority score based on multiple factors
            priority_score = 0
            
            # Factor 1: Recency (more recent = higher score)
            pub_date = datetime.strptime(news.get('published_at', ''), '%Y-%m-%d %H:%M:%S')
            days_old = (datetime.now() - pub_date).days
            priority_score += max(0, (30 - days_old)) / 30  # Max 1 point for recency
            
            # Factor 2: Sentiment impact (absolute value of sentiment)
            sentiment_value = abs(float(news.get('sentiment', 0)))
            priority_score += sentiment_value  # Max 1 point for sentiment
            
            # Factor 3: Source relevance
            if news.get('source') in ['Reuters', 'Bloomberg', 'CNBC', 'Financial Times']:
                priority_score += 1  # Trusted sources get extra point
            
            # Factor 4: Title relevance
            title = news.get('title', '').lower()
            relevant_keywords = ['earnings', 'profit', 'revenue', 'growth', 'dividend',
                               'merger', 'acquisition', 'stock', 'shares', 'market']
            keyword_matches = sum(1 for keyword in relevant_keywords if keyword in title)
            priority_score += min(1, keyword_matches / 3)  # Max 1 point for keywords
            
            # Add processed news item with priority score
            processed_news.append({
                'title': news.get('title'),
                'description': news.get('description'),
                'published_at': news.get('published_at'),
                'url': news.get('url'),
                'source': news.get('source'),
                'sentiment': float(news.get('sentiment', 0)),
                'priority_score': priority_score
            })
        
        # Sort news by priority score
        processed_news.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Calculate weighted sentiment score
        if processed_news:
            weighted_sentiment = sum(news['sentiment'] * news['priority_score'] 
                                  for news in processed_news) / sum(news['priority_score'] 
                                  for news in processed_news)
        else:
            weighted_sentiment = 0
        
        # Update cache
        st.session_state.news_cache[symbol] = {
            'timestamp': current_time,
            'sentiment': weighted_sentiment,
            'news': processed_news
        }
        st.session_state.last_fetch_time = current_time
        
        return weighted_sentiment, processed_news
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            st.error("Invalid API key. Please check your MarketAux API key in the sidebar.")
        else:
            st.error(f"Error fetching news data: {str(e)}")
        return 0, []
    except Exception as e:
        st.error(f"Error fetching news data: {str(e)}")
        return 0, []

def display_news_section(news_items):
    """Display news items with enhanced visualization"""
    if not news_items:
        st.info("No news items found for this stock.")
        return
    
    # Create tabs for different news categories
    tabs = st.tabs(["All News", "High Impact", "Recent News"])
    
    with tabs[0]:  # All News
        for news in news_items:
            with st.expander(f"📰 {news['title']} (Priority: {news['priority_score']:.2f})"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Source:** {news['source']}")
                    st.write(f"**Published:** {news['published_at']}")
                with col2:
                    sentiment_color = 'green' if news['sentiment'] > 0 else 'red'
                    st.markdown(f"**Sentiment:** <span style='color:{sentiment_color}'>{news['sentiment']:.2f}</span>", 
                              unsafe_allow_html=True)
                st.write(news['description'])
                st.markdown(f"[Read more]({news['url']})")
    
    with tabs[1]:  # High Impact
        high_impact_news = [n for n in news_items if abs(n['sentiment']) > 0.3]
        if high_impact_news:
            for news in high_impact_news:
                with st.expander(f"💥 {news['title']} (Impact: {abs(news['sentiment']):.2f})"):
                    st.write(f"**Source:** {news['source']}")
                    st.write(f"**Published:** {news['published_at']}")
                    st.write(news['description'])
                    st.markdown(f"[Read more]({news['url']})")
        else:
            st.info("No high-impact news found.")
    
    with tabs[2]:  # Recent News
        recent_news = [n for n in news_items 
                      if (datetime.now() - datetime.strptime(n['published_at'], 
                      '%Y-%m-%d %H:%M:%S')).days <= 7]
        if recent_news:
            for news in recent_news:
                with st.expander(f"🕒 {news['title']}"):
                    st.write(f"**Source:** {news['source']}")
                    st.write(f"**Published:** {news['published_at']}")
                    st.write(news['description'])
                    st.markdown(f"[Read more]({news['url']})")
        else:
            st.info("No recent news found.")

# Update the main container section in main():
with main_container:
    # Display sentiment score with enhanced visualization
    col1, col2 = st.columns([1, 2])
    with col1:
        sentiment_color = 'green' if sentiment_score > 0 else 'red' if sentiment_score < 0 else 'gray'
        st.markdown(f"""
        <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px;'>
            <h3>Overall Sentiment Score</h3>
            <h2 style='color: {sentiment_color}'>{sentiment_score:.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Display news items with the new display function
    display_news_section(news_items)
