import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def fetch_price_data(symbol, period='1mo'):
    """
    Fetch price data from Yahoo Finance
    Add .SA suffix for Saudi stocks
    """
    try:
        ticker = yf.Ticker(f"{symbol}.SA")
        df = ticker.history(period=period)
        return df
    except Exception as e:
        print(f"Error fetching price data for {symbol}: {e}")
        return None

def calculate_technical_indicators(df):
    """Calculate various technical indicators"""
    if df is None or df.empty:
        return None
    
    # Copy dataframe to avoid modifications
    df = df.copy()
    
    # RSI
    def calculate_rsi(data, periods=14):
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    # MACD
    def calculate_macd(data):
        exp1 = data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = data['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        return macd, signal
    
    # Bollinger Bands
    def calculate_bollinger_bands(data, window=20):
        ma = data['Close'].rolling(window=window).mean()
        std = data['Close'].rolling(window=window).std()
        upper = ma + (std * 2)
        lower = ma - (std * 2)
        return upper, lower
    
    # Calculate indicators
    df['RSI'] = calculate_rsi(df)
    df['MACD'], df['Signal'] = calculate_macd(df)
    df['BB_Upper'], df['BB_Lower'] = calculate_bollinger_bands(df)
    
    # Volume indicators
    df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
    df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']
    
    # Price momentum
    df['Price_Momentum'] = df['Close'].pct_change(periods=5)
    
    # Support and Resistance
    df['20_day_high'] = df['High'].rolling(window=20).max()
    df['20_day_low'] = df['Low'].rolling(window=20).min()
    
    return df
