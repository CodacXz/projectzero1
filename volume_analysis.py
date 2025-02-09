import pandas as pd
import numpy as np

def analyze_volume_patterns(df):
    """Analyze trading volume patterns"""
    if df is None or df.empty:
        return None
    
    analysis = {}
    
    # Volume trend
    recent_volume = df['Volume'].tail(5).mean()
    historical_volume = df['Volume'].mean()
    analysis['volume_trend'] = recent_volume / historical_volume
    
    # Volume spikes
    volume_std = df['Volume'].std()
    volume_mean = df['Volume'].mean()
    analysis['volume_spikes'] = len(df[df['Volume'] > volume_mean + 2 * volume_std])
    
    # Price-volume correlation
    analysis['price_volume_correlation'] = df['Close'].corr(df['Volume'])
    
    # Volume consistency
    analysis['volume_consistency'] = volume_std / volume_mean
    
    # Buying/Selling pressure
    df['Price_Change'] = df['Close'] - df['Open']
    up_volume = df[df['Price_Change'] > 0]['Volume'].sum()
    down_volume = df[df['Price_Change'] < 0]['Volume'].sum()
    analysis['buying_pressure'] = up_volume / (up_volume + down_volume)
    
    return analysis
