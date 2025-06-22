"""
ASX Trading Service

This module provides specialized functionality for trading ASX stocks through a brokerage.
It handles the specific requirements for Australian market trading.
"""

import os
import logging
import time
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from brokerage_connector import AlpacaConnector
from logger_config import setup_logger
from utils import is_asx_trading_hours, format_currency

# Set up logging
logger = setup_logger()

# Load environment variables
load_dotenv()

# Australian Eastern Time Zone
AUSTRALIA_TZ = pytz.timezone('Australia/Sydney')

class ASXTradingService:
    """
    Service for trading ASX stocks through a brokerage API
    """
    
    def __init__(self, use_sandbox=True):
        """
        Initialize the ASX trading service
        
        Args:
            use_sandbox (bool): Whether to use sandbox/paper trading mode
        """
        self.use_sandbox = use_sandbox
        self.brokerage = None
        self.is_connected = False
        self.brokerage_type = os.getenv('BROKERAGE_TYPE', 'alpaca')
        
        # Initialize the brokerage connection
        self._initialize_brokerage()
    
    def _initialize_brokerage(self):
        """Initialize the appropriate brokerage connection based on environment settings"""
        try:
            if self.brokerage_type.lower() == 'alpaca':
                self.brokerage = AlpacaConnector(sandbox_mode=self.use_sandbox)
                self.is_connected = True
                logger.info(f"Connected to {'sandbox' if self.use_sandbox else 'live'} Alpaca API")
            else:
                logger.error(f"Unsupported brokerage type: {self.brokerage_type}")
                raise ValueError(f"Unsupported brokerage type: {self.brokerage_type}")
        except Exception as e:
            logger.error(f"Failed to initialize brokerage connection: {str(e)}")
            self.is_connected = False
            raise
    
    def get_account_info(self):
        """
        Get account information from the brokerage
        
        Returns:
            dict: Account information
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to brokerage API")
        
        try:
            return self.brokerage.get_account()
        except Exception as e:
            logger.error(f"Error getting account information: {str(e)}")
            raise
    
    def get_market_status(self):
        """
        Get the current status of the ASX market
        
        Returns:
            dict: Market status information
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to brokerage API")
        
        try:
            # For Alpaca, we need to adjust for ASX trading hours
            # since Alpaca primarily tracks US markets
            clock = self.brokerage.get_clock()
            
            # Check if current time is within ASX trading hours
            now = datetime.now(AUSTRALIA_TZ)
            is_asx_open = is_asx_trading_hours()
            
            next_open_close = self._get_next_asx_session()
            
            return {
                'timestamp': now.isoformat(),
                'is_open': is_asx_open,
                'next_open': next_open_close['next_open'].isoformat() if next_open_close.get('next_open') else None,
                'next_close': next_open_close['next_close'].isoformat() if next_open_close.get('next_close') else None
            }
        except Exception as e:
            logger.error(f"Error getting market status: {str(e)}")
            raise
    
    def _get_next_asx_session(self):
        """
        Calculate the next ASX trading session opening and closing times
        
        Returns:
            dict: Next open and close times
        """
        now = datetime.now(AUSTRALIA_TZ)
        current_day = now.weekday()  # Monday is 0, Sunday is 6
        current_time = now.time()
        
        # ASX trading hours: 10:00 AM - 4:00 PM Sydney time, Monday to Friday
        market_open_time = datetime.strptime('10:00', '%H:%M').time()
        market_close_time = datetime.strptime('16:00', '%H:%M').time()
        
        result = {}
        
        # If it's before market open on a weekday
        if current_day < 5 and current_time < market_open_time:
            next_open = datetime.combine(now.date(), market_open_time).replace(tzinfo=AUSTRALIA_TZ)
            next_close = datetime.combine(now.date(), market_close_time).replace(tzinfo=AUSTRALIA_TZ)
            result['next_open'] = next_open
            result['next_close'] = next_close
        
        # If it's after market close on a weekday (but not Friday)
        elif current_day < 4 and current_time > market_close_time:
            next_day = now.date() + timedelta(days=1)
            next_open = datetime.combine(next_day, market_open_time).replace(tzinfo=AUSTRALIA_TZ)
            next_close = datetime.combine(next_day, market_close_time).replace(tzinfo=AUSTRALIA_TZ)
            result['next_open'] = next_open
            result['next_close'] = next_close
        
        # If it's Friday after market close or weekend
        elif (current_day == 4 and current_time > market_close_time) or current_day >= 5:
            # Calculate days until Monday
            days_until_monday = (7 - current_day) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            
            next_day = now.date() + timedelta(days=days_until_monday)
            next_open = datetime.combine(next_day, market_open_time).replace(tzinfo=AUSTRALIA_TZ)
            next_close = datetime.combine(next_day, market_close_time).replace(tzinfo=AUSTRALIA_TZ)
            result['next_open'] = next_open
            result['next_close'] = next_close
        
        # If market is currently open
        elif current_day < 5 and market_open_time <= current_time <= market_close_time:
            next_close = datetime.combine(now.date(), market_close_time).replace(tzinfo=AUSTRALIA_TZ)
            result['next_close'] = next_close
            
            # Calculate next open (next day or Monday)
            if current_day < 4:  # Monday-Thursday
                next_day = now.date() + timedelta(days=1)
            else:  # Friday
                next_day = now.date() + timedelta(days=3)  # Skip to Monday
            
            next_open = datetime.combine(next_day, market_open_time).replace(tzinfo=AUSTRALIA_TZ)
            result['next_open'] = next_open
        
        return result
    
    def get_positions(self):
        """
        Get current positions from the brokerage
        
        Returns:
            list: Current positions
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to brokerage API")
        
        try:
            return self.brokerage.get_positions()
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            raise
    
    def get_orders(self, status=None, limit=None):
        """
        Get orders from the brokerage
        
        Args:
            status (str, optional): Order status filter
            limit (int, optional): Maximum number of orders to return
            
        Returns:
            list: Orders
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to brokerage API")
        
        try:
            return self.brokerage.get_orders(status=status, limit=limit)
        except Exception as e:
            logger.error(f"Error getting orders: {str(e)}")
            raise
    
    def check_stock_shortable(self, symbol):
        """
        Check if a stock is available for shorting
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            bool: Whether the stock is shortable
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to brokerage API")
        
        try:
            # For ASX stocks, add .AX suffix if not present
            if not symbol.endswith('.AX') and not '.' in symbol:
                symbol = f"{symbol}.AX"
            
            asset = self.brokerage.get_asset(symbol)
            return asset.get('shortable', False)
        except Exception as e:
            logger.error(f"Error checking if {symbol} is shortable: {str(e)}")
            return False
    
    def open_short_position(self, symbol, quantity, order_type='market', 
                            time_in_force='day', limit_price=None, stop_price=None):
        """
        Open a short position
        
        Args:
            symbol (str): Stock symbol
            quantity (int): Number of shares to short
            order_type (str): Order type ('market', 'limit', 'stop', 'stop_limit')
            time_in_force (str): Time in force ('day', 'gtc', 'ioc', 'fok')
            limit_price (float, optional): Limit price for limit orders
            stop_price (float, optional): Stop price for stop orders
            
        Returns:
            dict: Order information
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to brokerage API")
        
        try:
            # For ASX stocks, add .AX suffix if not present
            if not symbol.endswith('.AX') and not '.' in symbol:
                symbol = f"{symbol}.AX"
            
            # Check if the stock is shortable
            if not self.check_stock_shortable(symbol):
                raise ValueError(f"{symbol} is not available for shorting")
            
            # Place the order
            order = self.brokerage.place_order(
                symbol=symbol,
                qty=quantity,
                side='sell',
                type=order_type,
                time_in_force=time_in_force,
                limit_price=limit_price,
                stop_price=stop_price
            )
            
            logger.info(f"Opened short position for {symbol}: {quantity} shares")
            return order
        except Exception as e:
            logger.error(f"Error opening short position for {symbol}: {str(e)}")
            raise
    
    def close_short_position(self, symbol, quantity=None):
        """
        Close a short position
        
        Args:
            symbol (str): Stock symbol
            quantity (int, optional): Number of shares to cover. If None, close the entire position.
            
        Returns:
            dict: Order information
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to brokerage API")
        
        try:
            # For ASX stocks, add .AX suffix if not present
            if not symbol.endswith('.AX') and not '.' in symbol:
                symbol = f"{symbol}.AX"
            
            if quantity is None:
                # Close the entire position
                order = self.brokerage.close_position(symbol)
            else:
                # Close a specific quantity
                positions = self.get_positions()
                position = next((p for p in positions if p['symbol'] == symbol), None)
                
                if not position:
                    raise ValueError(f"No position found for {symbol}")
                
                if abs(int(position['qty'])) < quantity:
                    raise ValueError(f"Requested quantity {quantity} exceeds position size {abs(int(position['qty']))}")
                
                order = self.brokerage.place_order(
                    symbol=symbol,
                    qty=quantity,
                    side='buy',  # Buy to cover the short
                    type='market',
                    time_in_force='day'
                )
            
            logger.info(f"Closed short position for {symbol}")
            return order
        except Exception as e:
            logger.error(f"Error closing short position for {symbol}: {str(e)}")
            raise
    
    def get_order_status(self, order_id):
        """
        Get the status of an order
        
        Args:
            order_id (str): Order ID
            
        Returns:
            dict: Order information
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to brokerage API")
        
        try:
            return self.brokerage.get_order(order_id)
        except Exception as e:
            logger.error(f"Error getting order status for order {order_id}: {str(e)}")
            raise
    
    def cancel_order(self, order_id):
        """
        Cancel an order
        
        Args:
            order_id (str): Order ID
            
        Returns:
            bool: Whether the cancellation was successful
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to brokerage API")
        
        try:
            self.brokerage.api.cancel_order(order_id)
            logger.info(f"Cancelled order {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {str(e)}")
            return False
    
    def wait_for_order_fill(self, order_id, timeout=60, check_interval=2):
        """
        Wait for an order to be filled
        
        Args:
            order_id (str): Order ID
            timeout (int): Maximum time to wait in seconds
            check_interval (int): Time between status checks in seconds
            
        Returns:
            dict: Final order status or None if timeout
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to brokerage API")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                order = self.brokerage.get_order(order_id)
                status = order.get('status')
                
                if status in ['filled', 'canceled', 'rejected', 'expired']:
                    logger.info(f"Order {order_id} final status: {status}")
                    return order
                
                logger.debug(f"Order {order_id} current status: {status}")
                time.sleep(check_interval)
            except Exception as e:
                logger.error(f"Error checking order status: {str(e)}")
                time.sleep(check_interval)
        
        logger.warning(f"Timeout waiting for order {order_id} to fill")
        return None