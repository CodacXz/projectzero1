import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.price_data import fetch_price_data, calculate_technical_indicators
from utils.volume_analysis import analyze_volume_patterns
from utils.market_analysis import analyze_market_correlations, calculate_market_score

# ... (previous imports and configurations) ...

def create_technical_chart(price_data):
    """Create technical analysis chart"""
    fig = go.Figure()
    
    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=price_data.index,
        open=price_data['Open'],
        high=price_data['High'],
        low=price_data['Low'],
        close=price_data['Close'],
        name='Price'
    ))
    
    # Add Bollinger Bands
    fig.add_trace(go.Scatter(
        x=price_data.index,
        y=price_data['BB_Upper'],
        name='BB Upper',
        line=dict(color='gray', dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=price_data.index,
        y=price_data['BB_Lower'],
        name='BB Lower',
        line=dict(color='gray', dash='dash'),
        fill='tonexty'
    ))
    
    return fig

def main():
    st.title("🇸🇦 Advanced Saudi Market Trading Assistant")
    
    # Sidebar filters
    st.sidebar.header("Analysis Settings")
    analysis_period = st.sidebar.selectbox(
        "Analysis Period",
        options=['1mo', '3mo', '6mo', '1y'],
        index=0
    )
    
    min_mentions = st.sidebar.slider("Minimum News Mentions", 1, 20, 1)
    min_sentiment = st.sidebar.slider("Minimum Sentiment Score", -1.0, 1.0, 0.0)
    
    if st.button("Analyze Market"):
        with st.spinner("Performing comprehensive market analysis..."):
            # Fetch news and sentiment data
            news_data = fetch_news()
            
            if news_data and "data" in news_data:
                # Process entities and create sentiment summary
                sentiment_df = create_sentiment_summary(all_entities)
                
                # Fetch price data for all symbols
                price_data_dict = {}
                technical_indicators_dict = {}
                volume_analysis_dict = {}
                
                for symbol in sentiment_df['symbol'].unique():
                    price_data = fetch_price_data(symbol, analysis_period)
                    if price_data is not None:
                        technical_indicators = calculate_technical_indicators(price_data)
                        volume_analysis = analyze_volume_patterns(price_data)
                        
                        price_data_dict[symbol] = price_data
                        technical_indicators_dict[symbol] = technical_indicators
                        volume_analysis_dict[symbol] = volume_analysis
                
                # Market correlation analysis
                market_correlations = analyze_market_correlations(price_data_dict)
                
                # Display comprehensive analysis for each stock
                st.header("💹 Comprehensive Trading Analysis")
                
                for _, row in sentiment_df.iterrows():
                    symbol = row['symbol']
                    
                    if symbol in price_data_dict:
                        with st.expander(f"{row['company_name']} ({symbol})"):
                            col1, col2, col3 = st.columns(3)
                            
                            # Sentiment metrics
                            col1.metric("Sentiment Score", f"{row['avg_sentiment']:.3f}")
                            col1.metric("News Volume", row['mention_count'])
                            
                            # Technical metrics
                            technical_data = technical_indicators_dict[symbol]
                            latest_tech = technical_data.iloc[-1]
                            col2.metric("RSI", f"{latest_tech['RSI']:.1f}")
                            col2.metric("MACD", f"{latest_tech['MACD']:.3f}")
                            
                            # Volume metrics
                            volume_data = volume_analysis_dict[symbol]
                            col3.metric("Volume Trend", f"{volume_data['volume_trend']:.2f}")
                            col3.metric("Buying Pressure", f"{volume_data['buying_pressure']:.2f}")
                            
                            # Technical Analysis Chart
                            st.plotly_chart(create_technical_chart(technical_data))
                            
                            # Trading Signals
                            st.subheader("🎯 Trading Signals")
                            
                            # Calculate overall score
                            market_score = calculate_market_score(
                                row['avg_sentiment'],
                                latest_tech['RSI']/100,
                                volume_data['buying_pressure'],
                                market_correlations['betas'].get(symbol, {})
                            )
                            
                            signal_col1, signal_col2 = st.columns(2)
                            
                            signal_col1.metric(
                                "Overall Score",
                                f"{market_score:.2f}",
                                delta=f"{row['sentiment_momentum']:.3f}"
                            )
                            
                            # Trading recommendation
                            recommendation = "Strong Buy" if market_score > 0.7 else \
                                           "Buy" if market_score > 0.5 else \
                                           "Hold" if market_score > 0.3 else \
                                           "Sell" if market_score > 0.2 else "Strong Sell"
                            
                            signal_col2.metric("Recommendation", recommendation)
                            
                            # Risk Analysis
                            st.subheader("⚠️ Risk Analysis")
                            risk_factors = pd.DataFrame({
                                'Factor': ['Sentiment Volatility', 'Price Volatility', 'Volume Consistency', 'Market Beta'],
                                'Value': [
                                    row['sentiment_volatility'],
                                    technical_data['Close'].std() / technical_data['Close'].mean(),
                                    volume_data['volume_consistency'],
                                    market_correlations['betas'].get(symbol, {}).get('beta', 0)
                                ]
                            })
                            st.table(risk_factors)
                
                # Market Overview
                st.header("🌐 Market Overview")
                
                # Correlation Heatmap
                st.plotly_chart(px.imshow(
                    market_correlations['correlation_matrix'],
                    title='Stock Correlation Matrix'
                ))
                
                # Market Leaders and Laggards
                st.subheader("Market Leaders and Laggards")
                leaders_df = sentiment_df.sort_values('avg_sentiment', ascending=False)
                st.table(leaders_df[['symbol', 'company_name', 'avg_sentiment', 'mention_count']].head())

if __name__ == "__main__":
    main()
