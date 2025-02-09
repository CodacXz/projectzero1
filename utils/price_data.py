import yfinance as yf
import pandas as pd
import numpy as np

def fetch_price_data(symbol, period):
    """
    Fetch stock price data from Yahoo Finance
    """
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period)
        if df.empty:
            return None
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def calculate_technical_indicators(df):
    """
    Calculate technical indicators for the given dataframe
    """
    # Bollinger Bands
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['20dSTD'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['MA20'] + (df['20dSTD'] * 2)
    df['BB_Lower'] = df['MA20'] - (df['20dSTD'] * 2)

    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Volume Ratio (comparing to 20-day average)
    df['Volume_Ratio'] = df['Volume'] / df['Volume'].rolling(window=20).mean()

    return df
