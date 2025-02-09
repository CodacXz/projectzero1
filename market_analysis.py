import pandas as pd
import numpy as np
from scipy import stats

def analyze_market_correlations(price_data_dict):
    """Analyze correlations between different stocks"""
    # Create correlation matrix of closing prices
    close_prices = pd.DataFrame()
    
    for symbol, data in price_data_dict.items():
        if data is not None and not data.empty:
            close_prices[symbol] = data['Close']
    
    correlation_matrix = close_prices.corr()
    
    # Calculate market beta for each stock
    market_returns = close_prices.pct_change()
    betas = {}
    
    for symbol in close_prices.columns:
        slope, _, r_value, _, _ = stats.linregress(
            market_returns.mean(axis=1),
            market_returns[symbol]
        )
        betas[symbol] = {
            'beta': slope,
            'r_squared': r_value ** 2
        }
    
    return {
        'correlation_matrix': correlation_matrix,
        'betas': betas
    }

def calculate_market_score(sentiment_score, technical_score, volume_score, correlation_data):
    """Calculate overall market score"""
    weights = {
        'sentiment': 0.3,
        'technical': 0.3,
        'volume': 0.2,
        'correlation': 0.2
    }
    
    correlation_score = 0.5  # Neutral base score
    if correlation_data and 'beta' in correlation_data:
        # Adjust score based on beta
        if correlation_data['beta'] < 0.8:
            correlation_score += 0.2  # Less volatile than market
        elif correlation_data['beta'] > 1.2:
            correlation_score -= 0.2  # More volatile than market
    
    final_score = (
        sentiment_score * weights['sentiment'] +
        technical_score * weights['technical'] +
        volume_score * weights['volume'] +
        correlation_score * weights['correlation']
    )
    
    return final_score
