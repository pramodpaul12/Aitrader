"""
Brokerage Connector Module

This module provides interfaces for connecting to different brokerage APIs.
Currently supports:
- Alpaca Markets API
"""

import os
import logging
from abc import ABC, abstractmethod
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv
from logger_config import setup_logger
from crypto_utils import CryptoUtils

# Load environment variables from .env file
load_dotenv()

# Set up logging
logger = setup_logger()
crypto = CryptoUtils()

class BrokerageConnector(ABC):
    """Abstract base class for brokerage connectors"""
    
    @abstractmethod
    def connect(self):
        """Establish connection to the brokerage API"""
        pass
    
    @abstractmethod
    def get_account(self):
        """Get account information"""
        pass
    
    @abstractmethod
    def get_positions(self):
        """Get current positions"""
        pass
    
    @abstractmethod
    def place_order(self, symbol, qty, side, type, time_in_force, limit_price=None, stop_price=None):
        """Place an order"""
        pass
    
    @abstractmethod
    def close_position(self, symbol):
        """Close a position for a specific symbol"""
        pass
    
    @abstractmethod
    def get_order(self, order_id):
        """Get information about a specific order"""
        pass
    
    @abstractmethod
    def get_orders(self, status=None, limit=None):
        """Get a list of orders"""
        pass
    
    @abstractmethod
    def get_asset(self, symbol):
        """Get asset information"""
        pass
    
    @abstractmethod
    def get_clock(self):
        """Get market clock information"""
        pass
    
    @abstractmethod
    def get_calendar(self, start=None, end=None):
        """Get market calendar"""
        pass


class AlpacaConnector(BrokerageConnector):
    """Connector for Alpaca Markets API"""
    
    def __init__(self, sandbox_mode=True):
        """
        Initialize Alpaca connector
        
        Args:
            sandbox_mode (bool): Whether to use the paper trading API (sandbox)
        """
        self.sandbox_mode = sandbox_mode
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.api_secret = os.getenv('ALPACA_API_SECRET')
        self.api = None
        
        if not self.api_key or not self.api_secret:
            logger.error("Alpaca API credentials not found in environment variables")
            raise ValueError("Alpaca API credentials not found. Please set ALPACA_API_KEY and ALPACA_API_SECRET environment variables.")
        
        self.connect()
    
    def connect(self):
        """Establish connection to Alpaca API"""
        try:
            # Use the paper trading API if in sandbox mode
            base_url = 'https://paper-api.alpaca.markets' if self.sandbox_mode else 'https://api.alpaca.markets'
            
            self.api = tradeapi.REST(
                key_id=self.api_key,
                secret_key=self.api_secret,
                base_url=base_url,
                api_version='v2'
            )
            
            # Verify connection by getting account information
            self.get_account()
            logger.info("Successfully connected to Alpaca API")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Alpaca API: {str(e)}")
            raise ConnectionError(f"Failed to connect to Alpaca API: {str(e)}")
    
    def get_account(self):
        """Get account information"""
        try:
            account = self.api.get_account()
            return {
                'id': account.id,
                'status': account.status,
                'equity': float(account.equity),
                'cash': float(account.cash),
                'buying_power': float(account.buying_power),
                'long_market_value': float(account.long_market_value),
                'short_market_value': float(account.short_market_value),
                'portfolio_value': float(account.portfolio_value),
                'pattern_day_trader': account.pattern_day_trader,
                'trading_blocked': account.trading_blocked,
                'account_blocked': account.account_blocked,
                'created_at': account.created_at
            }
        except Exception as e:
            logger.error(f"Error retrieving account information: {str(e)}")
            raise
    
    def get_positions(self):
        """Get current positions"""
        try:
            positions = self.api.list_positions()
            return [{
                'symbol': position.symbol,
                'qty': int(position.qty),
                'side': 'long' if int(position.qty) > 0 else 'short',
                'avg_entry_price': float(position.avg_entry_price),
                'market_value': float(position.market_value),
                'cost_basis': float(position.cost_basis),
                'unrealized_pl': float(position.unrealized_pl),
                'unrealized_plpc': float(position.unrealized_plpc),
                'current_price': float(position.current_price),
                'lastday_price': float(position.lastday_price),
                'change_today': float(position.change_today)
            } for position in positions]
        except Exception as e:
            logger.error(f"Error retrieving positions: {str(e)}")
            raise
    
    def place_order(self, symbol, qty, side, type='market', time_in_force='day', 
                    limit_price=None, stop_price=None):
        """
        Place an order
        
        Args:
            symbol (str): Asset symbol
            qty (int): Order quantity
            side (str): Order side ('buy' or 'sell')
            type (str): Order type ('market', 'limit', 'stop', 'stop_limit')
            time_in_force (str): Time in force ('day', 'gtc', 'ioc', 'fok')
            limit_price (float, optional): Limit price for limit orders
            stop_price (float, optional): Stop price for stop orders
            
        Returns:
            dict: Order information
        """
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=type,
                time_in_force=time_in_force,
                limit_price=limit_price,
                stop_price=stop_price
            )
            
            logger.info(f"Order placed: {order.id} for {symbol} ({side} {qty} shares)")
            
            return {
                'id': order.id,
                'client_order_id': order.client_order_id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'filled_qty': float(order.filled_qty) if hasattr(order, 'filled_qty') else 0,
                'side': order.side,
                'type': order.type,
                'time_in_force': order.time_in_force,
                'limit_price': float(order.limit_price) if order.limit_price else None,
                'stop_price': float(order.stop_price) if order.stop_price else None,
                'status': order.status,
                'created_at': order.created_at,
                'updated_at': order.updated_at if hasattr(order, 'updated_at') else None
            }
        except Exception as e:
            logger.error(f"Error placing order for {symbol}: {str(e)}")
            raise
    
    def close_position(self, symbol):
        """
        Close a position for a specific symbol
        
        Args:
            symbol (str): Asset symbol
            
        Returns:
            dict: Order information for the closing order
        """
        try:
            order = self.api.close_position(symbol)
            
            logger.info(f"Closed position for {symbol} with order {order.id}")
            
            return {
                'id': order.id,
                'client_order_id': order.client_order_id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'filled_qty': float(order.filled_qty) if hasattr(order, 'filled_qty') else 0,
                'side': order.side,
                'type': order.type,
                'time_in_force': order.time_in_force,
                'status': order.status,
                'created_at': order.created_at
            }
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {str(e)}")
            raise
    
    def get_order(self, order_id):
        """
        Get information about a specific order
        
        Args:
            order_id (str): Order ID
            
        Returns:
            dict: Order information
        """
        try:
            order = self.api.get_order(order_id)
            
            return {
                'id': order.id,
                'client_order_id': order.client_order_id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'filled_qty': float(order.filled_qty) if hasattr(order, 'filled_qty') else 0,
                'side': order.side,
                'type': order.type,
                'time_in_force': order.time_in_force,
                'limit_price': float(order.limit_price) if order.limit_price else None,
                'stop_price': float(order.stop_price) if order.stop_price else None,
                'status': order.status,
                'created_at': order.created_at,
                'updated_at': order.updated_at if hasattr(order, 'updated_at') else None
            }
        except Exception as e:
            logger.error(f"Error retrieving order {order_id}: {str(e)}")
            raise
    
    def get_orders(self, status=None, limit=None):
        """
        Get a list of orders
        
        Args:
            status (str, optional): Order status
            limit (int, optional): Maximum number of orders to return
            
        Returns:
            list: List of orders
        """
        try:
            orders = self.api.list_orders(status=status, limit=limit)
            
            return [{
                'id': order.id,
                'client_order_id': order.client_order_id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'filled_qty': float(order.filled_qty) if hasattr(order, 'filled_qty') else 0,
                'side': order.side,
                'type': order.type,
                'time_in_force': order.time_in_force,
                'limit_price': float(order.limit_price) if order.limit_price else None,
                'stop_price': float(order.stop_price) if order.stop_price else None,
                'status': order.status,
                'created_at': order.created_at,
                'updated_at': order.updated_at if hasattr(order, 'updated_at') else None
            } for order in orders]
        except Exception as e:
            logger.error(f"Error retrieving orders: {str(e)}")
            raise
    
    def get_asset(self, symbol):
        """
        Get asset information
        
        Args:
            symbol (str): Asset symbol
            
        Returns:
            dict: Asset information
        """
        try:
            asset = self.api.get_asset(symbol)
            
            return {
                'id': asset.id,
                'symbol': asset.symbol,
                'name': asset.name,
                'asset_class': asset.asset_class,
                'exchange': asset.exchange,
                'status': asset.status,
                'tradable': asset.tradable,
                'marginable': asset.marginable,
                'shortable': asset.shortable,
                'easy_to_borrow': asset.easy_to_borrow
            }
        except Exception as e:
            logger.error(f"Error retrieving asset information for {symbol}: {str(e)}")
            raise
    
    def get_clock(self):
        """
        Get market clock information
        
        Returns:
            dict: Market clock information
        """
        try:
            clock = self.api.get_clock()
            
            return {
                'timestamp': clock.timestamp,
                'is_open': clock.is_open,
                'next_open': clock.next_open,
                'next_close': clock.next_close
            }
        except Exception as e:
            logger.error(f"Error retrieving market clock information: {str(e)}")
            raise
    
    def get_calendar(self, start=None, end=None):
        """
        Get market calendar
        
        Args:
            start (str, optional): Start date in 'YYYY-MM-DD' format
            end (str, optional): End date in 'YYYY-MM-DD' format
            
        Returns:
            list: Market calendar
        """
        try:
            calendar = self.api.get_calendar(start=start, end=end)
            
            return [{
                'date': day.date,
                'open': day.open,
                'close': day.close
            } for day in calendar]
        except Exception as e:
            logger.error(f"Error retrieving market calendar: {str(e)}")
            raise