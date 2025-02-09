import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from utils.price_data import fetch_price_data, calculate_technical_indicators

# Set page config
st.set_page_config(
    page_title="Stock Market Analysis",
    page_icon="📈",
    layout="wide"
)

# Title and description
st.title("📈 Stock Market Technical Analysis")
st.markdown("Analyze Saudi stocks with technical indicators and market data")

# Sidebar
st.sidebar.header("Settings")
symbol_input = st.sidebar.text_input("Enter Stock Symbol (e.g., 2222):", "2222")
# Format the symbol for Saudi stocks
symbol = f"{symbol_input}.SR"

period = st.sidebar.selectbox(
    "Select Time Period:",
    ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=2
)

# Add some information about symbol format
st.sidebar.markdown("---")
st.sidebar.markdown("ℹ️ **Note:** Enter the stock number without '.SR'")
st.sidebar.markdown("Examples:")
st.sidebar.markdown("- Saudi Aramco: 2222")
st.sidebar.markdown("- Al Rajhi Bank: 1120")
st.sidebar.markdown("- SABIC: 2010")

# Debug information
st.sidebar.markdown(f"Fetching data for: {symbol}")

# Fetch and process data
@st.cache_data(ttl=3600)  # Cache data for 1 hour
def load_data(symbol, period):
    df = fetch_price_data(symbol, period)
    if df is not None:
        return calculate_technical_indicators(df)
    return None

# Load data
df = load_data(symbol, period)

if df is not None:
    # Create main price chart
    fig = make_subplots(rows=3, cols=1, 
                        shared_xaxes=True,
                        vertical_spacing=0.05,
                        row_heights=[0.5, 0.25, 0.25])

    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price'
        ),
        row=1, col=1
    )

    # Add Bollinger Bands
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['BB_Upper'],
            name='BB Upper',
            line=dict(color='gray', dash='dash')
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['BB_Lower'],
            name='BB Lower',
            line=dict(color='gray', dash='dash'),
            fill='tonexty'
        ),
        row=1, col=1
    )

    # MACD
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['MACD'],
            name='MACD',
            line=dict(color='blue')
        ),
        row=2, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['Signal'],
            name='Signal',
            line=dict(color='orange')
        ),
        row=2, col=1
    )

    # RSI
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['RSI'],
            name='RSI',
            line=dict(color='purple')
        ),
        row=3, col=1
    )

    # Add horizontal lines for RSI
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    # Update layout
    fig.update_layout(
        title=f"Technical Analysis for {symbol}",
        xaxis_title="Date",
        yaxis_title="Price",
        height=800,
        showlegend=True,
        xaxis_rangeslider_visible=False
    )

    # Display the chart
    st.plotly_chart(fig, use_container_width=True)

    # Display key statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Current Price",
            f"{df['Close'][-1]:.2f}",
            f"{df['Close'].pct_change()[-1]*100:.2f}%"
        )
    
    with col2:
        st.metric(
            "RSI",
            f"{df['RSI'][-1]:.2f}",
            "Overbought" if df['RSI'][-1] > 70 else "Oversold" if df['RSI'][-1] < 30 else "Neutral"
        )
    
    with col3:
        st.metric(
            "Volume Ratio",
            f"{df['Volume_Ratio'][-1]:.2f}",
            f"{(df['Volume_Ratio'][-1] - 1)*100:.2f}% vs avg"
        )

    # Technical Analysis Summary
    st.subheader("Technical Analysis Summary")
    
    # Create analysis summary
    analysis = []
    
    # RSI Analysis
    rsi = df['RSI'][-1]
    if rsi > 70:
        analysis.append("🔴 RSI indicates overbought conditions")
    elif rsi < 30:
        analysis.append("🟢 RSI indicates oversold conditions")
    else:
        analysis.append("⚪ RSI is neutral")

    # MACD Analysis
    if df['MACD'][-1] > df['Signal'][-1] and df['MACD'][-2] <= df['Signal'][-2]:
        analysis.append("🟢 MACD shows bullish crossover")
    elif df['MACD'][-1] < df['Signal'][-1] and df['MACD'][-2] >= df['Signal'][-2]:
        analysis.append("🔴 MACD shows bearish crossover")
    else:
        analysis.append("⚪ MACD shows no clear signal")

    # Bollinger Bands Analysis
    current_price = df['Close'][-1]
    if current_price > df['BB_Upper'][-1]:
        analysis.append("🔴 Price is above upper Bollinger Band - potential resistance")
    elif current_price < df['BB_Lower'][-1]:
        analysis.append("🟢 Price is below lower Bollinger Band - potential support")
    else:
        analysis.append("⚪ Price is within Bollinger Bands")

    # Display analysis points
    for point in analysis:
        st.markdown(point)

else:
    st.error(f"""
    Unable to fetch data for symbol: {symbol}
    Please check if:
    1. The symbol is correct
    2. You have internet connection
    3. The market is open or has historical data
    """)

# Footer
st.markdown("---")
st.markdown("Data provided by Yahoo Finance")
