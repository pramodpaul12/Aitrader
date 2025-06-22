import pandas as pd
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class StockAnalyzer:
    def __init__(self):
        """Initialize the stock analyzer."""
        pass
        
    def get_shorting_score(self, stock_data):
        """
        Calculate a score indicating how suitable a stock is for shorting.
        Higher score means better shorting opportunity.
        
        Args:
            stock_data (pandas.DataFrame): Historical stock data
            
        Returns:
            float: Shorting score from 0-100
        """
        try:
            if stock_data.empty:
                return 0
            
            # Calculate technical indicators
            stock_data = self._calculate_indicators(stock_data)
            
            # Initialize score
            score = 50  # Neutral starting point
            
            # 1. Trend analysis - Negative trend is good for shorting
            if 'SMA20' in stock_data.columns and 'SMA50' in stock_data.columns:
                latest = stock_data.iloc[-1]
                
                # If price is below short-term moving average, good for shorting
                if latest['Close'] < latest['SMA20']:
                    score += 10
                
                # If short-term MA is below long-term MA (death cross), good for shorting
                if latest['SMA20'] < latest['SMA50']:
                    score += 15
            
            # 2. Momentum indicators
            if 'RSI' in stock_data.columns:
                rsi = stock_data['RSI'].iloc[-1]
                
                # RSI above 70 indicates overbought, good for shorting
                if rsi > 70:
                    score += 15
                elif rsi > 60:
                    score += 10
                elif rsi < 30:  # Oversold, not good for shorting
                    score -= 15
            
            # 3. Volatility - Higher volatility, higher risk, but potentially better returns
            if len(stock_data) >= 5:
                recent_volatility = stock_data['Close'][-5:].pct_change().std() * 100
                if recent_volatility > 3:  # High volatility
                    score += 5
            
            # 4. Volume - Higher volume often indicates stronger trends
            if 'Volume' in stock_data.columns and len(stock_data) >= 5:
                avg_volume = stock_data['Volume'][-5:].mean()
                latest_volume = stock_data['Volume'].iloc[-1]
                
                # Higher than average volume can indicate stronger trend
                if latest_volume > avg_volume * 1.5:
                    score += 5
            
            # 5. Recent price action - Look for short-term reversals
            if len(stock_data) >= 3:
                last_3_days = stock_data['Close'][-3:].pct_change().dropna()
                
                # If recent days show price increases, might be good to short (reversion)
                if len(last_3_days) > 0 and last_3_days.mean() > 0.01:  # Average > 1% gain
                    score += 10
            
            # Make sure score is within 0-100 range
            score = max(0, min(100, score))
            
            logger.debug(f"Calculated shorting score: {score:.2f}")
            return score
            
        except Exception as e:
            logger.error(f"Error calculating shorting score: {str(e)}")
            return 0
    
    def _calculate_indicators(self, data):
        """
        Calculate technical indicators for analysis.
        
        Args:
            data (pandas.DataFrame): DataFrame containing stock data
            
        Returns:
            pandas.DataFrame: DataFrame with added indicators
        """
        df = data.copy()
        
        try:
            # 1. Moving Averages
            df['SMA20'] = df['Close'].rolling(window=20).mean()
            df['SMA50'] = df['Close'].rolling(window=50).mean()
            
            # 2. Relative Strength Index (RSI)
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # 3. Bollinger Bands
            df['20MA'] = df['Close'].rolling(window=20).mean()
            df['20SD'] = df['Close'].rolling(window=20).std()
            df['Upper_Band'] = df['20MA'] + (df['20SD'] * 2)
            df['Lower_Band'] = df['20MA'] - (df['20SD'] * 2)
            
            # 4. MACD (Moving Average Convergence Divergence)
            df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
            df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = df['EMA12'] - df['EMA26']
            df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
            
            # 5. Average True Range (ATR) for volatility
            high_low = df['High'] - df['Low']
            high_close = (df['High'] - df['Close'].shift()).abs()
            low_close = (df['Low'] - df['Close'].shift()).abs()
            
            true_ranges = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df['ATR'] = true_ranges.rolling(window=14).mean()
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            return data
    
    def get_recommendation(self, symbol, data=None):
        """
        Get a trading recommendation for a specific stock.
        
        Args:
            symbol (str): Stock symbol
            data (pandas.DataFrame, optional): Stock data if already available
            
        Returns:
            dict: Trading recommendation
        """
        try:
            # If data is not provided, return a neutral recommendation
            if data is None or data.empty:
                return {
                    'symbol': symbol,
                    'recommendation': 'NEUTRAL',
                    'confidence': 0,
                    'reason': 'Insufficient data'
                }
            
            # Calculate score
            score = self.get_shorting_score(data)
            
            # Generate recommendation based on score
            if score >= 70:
                recommendation = 'STRONG SHORT'
                confidence = 'HIGH'
                reason = 'Multiple indicators suggest a strong shorting opportunity'
            elif score >= 60:
                recommendation = 'SHORT'
                confidence = 'MEDIUM'
                reason = 'Favorable conditions for shorting'
            elif score <= 30:
                recommendation = 'AVOID SHORT'
                confidence = 'HIGH'
                reason = 'Unfavorable conditions for shorting'
            else:
                recommendation = 'NEUTRAL'
                confidence = 'LOW'
                reason = 'Mixed signals, no clear direction'
            
            return {
                'symbol': symbol,
                'recommendation': recommendation,
                'confidence': confidence,
                'score': score,
                'reason': reason,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendation for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'recommendation': 'ERROR',
                'confidence': 0,
                'reason': f'Error: {str(e)}'
            }
