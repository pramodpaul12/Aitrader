import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time
import random

logger = logging.getLogger(__name__)

class DataService:
    def __init__(self):
        """Initialize the data service for retrieving stock data."""
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = 60  # Cache duration in seconds
        from crypto_utils import CryptoUtils
        self.crypto = CryptoUtils()

    def get_stock_historical_data(self, symbol, period="1d", interval="1m"):
        """
        Retrieve historical data for a given stock symbol.
        
        Args:
            symbol (str): Stock symbol (e.g., 'CBA.AX')
            period (str): Period to retrieve ('1d', '5d', '1mo', '3mo', '6mo', '1y', etc.)
            interval (str): Data interval ('1m', '5m', '15m', '30m', '60m', '1d', etc.)
            
        Returns:
            pandas.DataFrame: DataFrame with historical stock data
        """
        try:
            cache_key = f"{symbol}_{period}_{interval}"
            current_time = time.time()
            
            # Check if we have cached data that's still valid
            if cache_key in self.cache and current_time - self.cache_expiry.get(cache_key, 0) < self.cache_duration:
                logger.debug(f"Retrieved {symbol} data from cache")
                return self.cache[cache_key]
            
            # Get data from yfinance
            stock = yf.Ticker(symbol)
            data = stock.history(period=period, interval=interval)
            
            # Validate data
            if data.empty:
                logger.warning(f"No data returned for {symbol}")
                raise ValueError(f"No data available for {symbol}")
            
            # Cache the data
            self.cache[cache_key] = data
            self.cache_expiry[cache_key] = current_time
            
            logger.info(f"Successfully retrieved {len(data)} data points for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error retrieving historical data for {symbol}: {str(e)}")
            raise

    def get_latest_stock_data(self, symbol):
        """
        Get the latest stock data for a given symbol.
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            dict: Dictionary containing latest stock data
        """
        try:
            # Get the most recent data point
            stock_data = self.get_stock_historical_data(symbol, period="1d", interval="1m")
            
            if stock_data.empty:
                raise ValueError(f"No data available for {symbol}")
            
            # Get the last data point
            latest_data = stock_data.iloc[-1]
            
            # Create a result dictionary
            result = {
                'symbol': symbol,
                'last_price': latest_data['Close'],
                'open': latest_data['Open'],
                'high': latest_data['High'],
                'low': latest_data['Low'],
                'volume': latest_data['Volume'],
                'timestamp': latest_data.name
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving latest data for {symbol}: {str(e)}")
            raise

    def get_asx_market_info(self):
        """
        Get information about the ASX market status.
        
        Returns:
            dict: Dictionary with market information
        """
        # ASX market hours: 10:00 AM to 4:00 PM AEST/AEDT (Sydney time)
        from datetime import datetime
        import pytz
        
        # Get current time in Sydney timezone
        sydney_tz = pytz.timezone('Australia/Sydney')
        sydney_time = datetime.now(sydney_tz)
        
        # Check if it's a weekday (0 = Monday, 4 = Friday)
        is_weekday = sydney_time.weekday() < 5
        
        # Check if it's during trading hours (10:00 AM to 4:00 PM)
        market_open_time = sydney_time.replace(hour=10, minute=0, second=0, microsecond=0)
        market_close_time = sydney_time.replace(hour=16, minute=0, second=0, microsecond=0)
        is_trading_hours = market_open_time <= sydney_time <= market_close_time
        
        # Determine market status
        if is_weekday and is_trading_hours:
            status = "OPEN"
        else:
            status = "CLOSED"
            
        # Calculate time until open or close
        if status == "OPEN":
            time_remaining = (market_close_time - sydney_time).total_seconds() / 60
            time_info = f"Closes in {int(time_remaining)} minutes"
        else:
            if not is_weekday:
                # Calculate days until Monday
                days_to_monday = (7 - sydney_time.weekday()) % 7
                next_trading_day = sydney_time + timedelta(days=days_to_monday)
                next_trading_day = next_trading_day.replace(hour=10, minute=0, second=0, microsecond=0)
            else:
                # Calculate time until market opens next day
                if sydney_time > market_close_time:
                    next_trading_day = sydney_time + timedelta(days=1)
                    next_trading_day = next_trading_day.replace(hour=10, minute=0, second=0, microsecond=0)
                else:
                    next_trading_day = market_open_time
                    
            time_delta = next_trading_day - sydney_time
            hours = time_delta.total_seconds() // 3600
            minutes = (time_delta.total_seconds() % 3600) // 60
            
            if hours > 24:
                days = int(hours // 24)
                hours = int(hours % 24)
                time_info = f"Opens in {days} days, {hours} hours"
            else:
                time_info = f"Opens in {int(hours)} hours, {int(minutes)} minutes"
        
        return {
            'status': status,
            'current_time': sydney_time.strftime('%Y-%m-%d %H:%M:%S'),
            'time_info': time_info,
            'is_trading_hours': is_trading_hours,
            'is_weekday': is_weekday
        }
