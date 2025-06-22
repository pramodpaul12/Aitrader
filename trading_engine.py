import pandas as pd
import numpy as np
from datetime import datetime
import logging
import streamlit as st
import os
from db_manager import DatabaseManager
from asx_trading_service import ASXTradingService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class TradingEngine:
    def __init__(self, data_service, analyzer):
        """
        Initialize the trading engine.
        
        Args:
            data_service: DataService instance for retrieving stock data
            analyzer: StockAnalyzer instance for analyzing stock data
        """
        self.data_service = data_service
        self.analyzer = analyzer
        self.db_manager = DatabaseManager()
        
        # Initialize real trading capabilities if enabled
        self.real_trading_enabled = os.getenv('ENABLE_REAL_TRADING', 'false').lower() == 'true'
        self.trading_service = None
        
        # If real trading is enabled and credentials are available, initialize the trading service
        if self.real_trading_enabled:
            try:
                use_sandbox = os.getenv('USE_TRADING_SANDBOX', 'true').lower() == 'true'
                self.trading_service = ASXTradingService(use_sandbox=use_sandbox)
                logger.info(f"Real trading initialized with {'sandbox' if use_sandbox else 'live'} mode")
            except Exception as e:
                logger.error(f"Failed to initialize real trading: {str(e)}")
                self.real_trading_enabled = False
        
    def open_position(self, symbol, position_size, current_price):
        """
        Open a new short position.
        
        Args:
            symbol (str): Stock symbol
            position_size (float): Position size in dollars
            current_price (float): Current price of the stock
        """
        try:
            # Calculate number of shares based on position size
            quantity = int(position_size / current_price)
            
            if quantity <= 0:
                raise ValueError("Position size too small to open a position")
            
            # Execute real trade if real trading is enabled
            order_info = None
            if self.real_trading_enabled and self.trading_service:
                logger.info(f"Executing real short order for {symbol}: {quantity} shares")
                try:
                    # Place the order through the brokerage
                    order_info = self.trading_service.open_short_position(
                        symbol=symbol,
                        quantity=quantity,
                        order_type='market'
                    )
                    
                    # Update current price if the order was filled
                    if order_info and order_info.get('status') == 'filled':
                        current_price = float(order_info.get('filled_avg_price', current_price))
                        logger.info(f"Order filled at price: ${current_price:.2f}")
                    
                    # Wait for order to fill if it's still pending
                    elif order_info and order_info.get('status') in ['new', 'accepted', 'pending_new']:
                        order_id = order_info.get('id')
                        logger.info(f"Waiting for order {order_id} to fill...")
                        
                        filled_order = self.trading_service.wait_for_order_fill(order_id, timeout=30)
                        if filled_order and filled_order.get('status') == 'filled':
                            current_price = float(filled_order.get('filled_avg_price', current_price))
                            logger.info(f"Order filled at price: ${current_price:.2f}")
                        else:
                            logger.warning(f"Order not filled within timeout, using estimated price")
                    
                except Exception as trading_error:
                    logger.error(f"Real trading error: {str(trading_error)}. Falling back to simulation.")
                    # Continue with simulation if real trading fails
            
            # Save position to database
            self.db_manager.set_current_position(
                symbol=symbol,
                entry_price=current_price,
                quantity=quantity,
                position_size=position_size
            )
            
            # Create position record for session state
            position = {
                'symbol': symbol,
                'entry_price': current_price,
                'quantity': quantity,
                'position_size': position_size,
                'entry_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'type': 'short',
                'order_id': order_info.get('id') if order_info else None,
                'real_trade': True if (self.real_trading_enabled and order_info) else False
            }
            
            # Update session state
            st.session_state.current_position = position
            
            # Log the transaction
            self._log_transaction(
                symbol=symbol,
                action="Short Open",
                price=current_price,
                quantity=quantity,
                pnl=0,
                reason="New position" + (" (REAL)" if (self.real_trading_enabled and order_info) else " (SIM)")
            )
            
            logger.info(f"Opened short position for {symbol}: {quantity} shares at ${current_price:.2f}")
            return position
            
        except Exception as e:
            logger.error(f"Error opening position for {symbol}: {str(e)}")
            raise
    
    def close_position(self, position, reason, current_price=None):
        """
        Close an existing position.
        
        Args:
            position (dict): The position to close
            reason (str): Reason for closing the position
            current_price (float, optional): Current price of the stock. If not provided, will be fetched.
        """
        try:
            symbol = position['symbol']
            entry_price = position['entry_price']
            quantity = position['quantity']
            order_id = position.get('order_id')
            is_real_trade = position.get('real_trade', False)
            
            # Execute real trade if this is a real position
            order_info = None
            if self.real_trading_enabled and self.trading_service and is_real_trade:
                logger.info(f"Executing real close order for {symbol}: {quantity} shares")
                try:
                    # Close the position through the brokerage
                    order_info = self.trading_service.close_short_position(
                        symbol=symbol,
                        quantity=quantity
                    )
                    
                    # Update current price if the order was filled
                    if order_info and order_info.get('status') == 'filled':
                        current_price = float(order_info.get('filled_avg_price', current_price))
                        logger.info(f"Close order filled at price: ${current_price:.2f}")
                    
                    # Wait for order to fill if it's still pending
                    elif order_info and order_info.get('status') in ['new', 'accepted', 'pending_new']:
                        close_order_id = order_info.get('id')
                        logger.info(f"Waiting for close order {close_order_id} to fill...")
                        
                        filled_order = self.trading_service.wait_for_order_fill(close_order_id, timeout=30)
                        if filled_order and filled_order.get('status') == 'filled':
                            current_price = float(filled_order.get('filled_avg_price', current_price))
                            logger.info(f"Close order filled at price: ${current_price:.2f}")
                        else:
                            logger.warning(f"Close order not filled within timeout, using estimated price")
                    
                except Exception as trading_error:
                    logger.error(f"Real trading error on close: {str(trading_error)}. Using simulation price.")
                    # Get the latest price from the data service if real trading fails
                    if current_price is None:
                        current_price = self.data_service.get_latest_stock_data(symbol)['last_price']
            else:
                # Get current price if not provided for simulation
                if current_price is None:
                    current_price = self.data_service.get_latest_stock_data(symbol)['last_price']
            
            # Calculate profit/loss for a short position
            # For a short: profit when close_price < entry_price
            pnl = (entry_price - current_price) * quantity
            
            # Update account balance
            settings = self.db_manager.get_account_settings()
            new_balance = settings['current_balance'] + pnl
            self.db_manager.update_account_settings(current_balance=new_balance)
            
            # Update session state balance
            st.session_state.account_balance += pnl
            
            # Log the transaction
            self._log_transaction(
                symbol=symbol,
                action="Short Close",
                price=current_price,
                quantity=quantity,
                pnl=pnl,
                reason=reason + (" (REAL)" if (is_real_trade and order_info) else " (SIM)")
            )
            
            # Clear current position in database
            self.db_manager.clear_current_position()
            
            # Clear current position in session state
            st.session_state.current_position = None
            
            logger.info(f"Closed short position for {symbol}: {quantity} shares at ${current_price:.2f}, P/L: ${pnl:.2f}")
            return pnl
            
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            raise
    
    def _log_transaction(self, symbol, action, price, quantity, pnl, reason):
        """
        Log a trading transaction to history.
        
        Args:
            symbol (str): Stock symbol
            action (str): Action taken (e.g., "Short Open", "Short Close")
            price (float): Transaction price
            quantity (int): Number of shares
            pnl (float): Profit/loss from the transaction
            reason (str): Reason for the transaction
        """
        # Add to database
        self.db_manager.add_trading_record(
            symbol=symbol,
            action=action,
            price=price,
            quantity=quantity,
            pnl=pnl,
            reason=reason
        )
        
        # Create transaction for session state
        transaction = {
            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Stock': symbol,
            'Action': action,
            'Price': price,
            'Quantity': quantity,
            'P/L': pnl,
            'Reason': reason
        }
        
        # Add to trading history in session state
        st.session_state.trading_history = pd.concat([
            st.session_state.trading_history,
            pd.DataFrame([transaction])
        ], ignore_index=True)
        
        logger.info(f"Logged transaction: {transaction}")
        
    def get_next_stock_for_trading(self, current_symbol=None):
        """
        Get the next stock to trade from the watch list.
        If a current symbol is provided, return the next one in the list.
        
        Args:
            current_symbol (str, optional): Current stock symbol
            
        Returns:
            dict: The next stock to trade or None if none available
        """
        try:
            # Get stock watch list from database
            stocks = self.db_manager.get_stock_watchlist()
            
            if not stocks:
                return None
                
            # If no current symbol, return the first stock
            if current_symbol is None:
                return stocks[0]
                
            # Find current stock in list
            current_index = -1
            for i, stock in enumerate(stocks):
                if stock['symbol'] == current_symbol:
                    current_index = i
                    break
                    
            # If found, return the next stock or wrap around
            if current_index >= 0:
                next_index = (current_index + 1) % len(stocks)
                return stocks[next_index]
            else:
                # Current stock not in list, return first stock
                return stocks[0]
                
        except Exception as e:
            logger.error(f"Error getting next stock for trading: {str(e)}")
            return None
            
    def is_real_trading_available(self):
        """
        Check if real trading is available (enabled and connected to brokerage).
        
        Returns:
            bool: Whether real trading is available
        """
        return self.real_trading_enabled and self.trading_service is not None and self.trading_service.is_connected
        
    def get_brokerage_account_info(self):
        """
        Get account information from the brokerage.
        
        Returns:
            dict: Account information or None if not connected
        """
        if not self.is_real_trading_available():
            return None
            
        try:
            return self.trading_service.get_account_info()
        except Exception as e:
            logger.error(f"Error getting brokerage account info: {str(e)}")
            return None
            
    def get_brokerage_positions(self):
        """
        Get current positions from the brokerage.
        
        Returns:
            list: Current positions or None if not connected
        """
        if not self.is_real_trading_available():
            return None
            
        try:
            return self.trading_service.get_positions()
        except Exception as e:
            logger.error(f"Error getting brokerage positions: {str(e)}")
            return None
            
    def get_real_trading_status(self):
        """
        Get the status of real trading including brokerage connection.
        
        Returns:
            dict: Status information
        """
        status = {
            'enabled': self.real_trading_enabled,
            'connected': False,
            'mode': 'simulation',
            'account_info': None,
            'error': None
        }
        
        if self.real_trading_enabled:
            try:
                if self.trading_service and self.trading_service.is_connected:
                    status['connected'] = True
                    status['mode'] = 'sandbox' if self.trading_service.use_sandbox else 'live'
                    
                    # Try to get account info
                    try:
                        status['account_info'] = self.trading_service.get_account_info()
                    except Exception as e:
                        status['error'] = f"Connected but error getting account info: {str(e)}"
                else:
                    status['error'] = "Trading enabled but not connected to brokerage"
            except Exception as e:
                status['error'] = f"Error checking trading service: {str(e)}"
                
        return status
