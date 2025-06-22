import os
import logging
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

# Setup logging
logger = logging.getLogger(__name__)

# Get database URL from environment variable
DATABASE_URL = os.environ.get("DATABASE_URL")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create base class for declarative models
Base = declarative_base()

# Define models
class StockWatchList(Base):
    __tablename__ = "stock_watchlist"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, unique=True)
    last_price = Column(Float)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "last_price": self.last_price,
            "added_at": self.added_at.strftime("%Y-%m-%d %H:%M:%S") if self.added_at else None
        }

class TradingHistory(Base):
    __tablename__ = "trading_history"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    symbol = Column(String(20), nullable=False)
    action = Column(String(20), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    pnl = Column(Float)
    reason = Column(String(100))
    
    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None,
            "symbol": self.symbol,
            "action": self.action,
            "price": self.price,
            "quantity": self.quantity,
            "pnl": self.pnl,
            "reason": self.reason
        }

class AccountSettings(Base):
    __tablename__ = "account_settings"
    
    id = Column(Integer, primary_key=True)
    initial_balance = Column(Float, default=10000.0)
    current_balance = Column(Float, default=10000.0)
    take_profit_pct = Column(Float, default=2.0)
    stop_loss_pct = Column(Float, default=1.0)
    position_size_pct = Column(Float, default=10.0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "initial_balance": self.initial_balance,
            "current_balance": self.current_balance,
            "take_profit_pct": self.take_profit_pct,
            "stop_loss_pct": self.stop_loss_pct,
            "position_size_pct": self.position_size_pct,
            "last_updated": self.last_updated.strftime("%Y-%m-%d %H:%M:%S") if self.last_updated else None
        }

class CurrentPosition(Base):
    __tablename__ = "current_position"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    entry_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    position_size = Column(Float, nullable=False)
    entry_time = Column(DateTime, default=datetime.utcnow)
    position_type = Column(String(10), default="short")
    
    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "entry_price": self.entry_price,
            "quantity": self.quantity,
            "position_size": self.position_size,
            "entry_time": self.entry_time.strftime("%Y-%m-%d %H:%M:%S") if self.entry_time else None,
            "type": self.position_type
        }

# Create all tables in the database
Base.metadata.create_all(engine)

# Create Session class for database interactions
Session = sessionmaker(bind=engine)

class DatabaseManager:
    def __init__(self):
        """Initialize the database manager."""
        self.engine = engine
        self.Session = Session
    
    def get_session(self):
        """Get a new session for database operations."""
        return self.Session()
    
    # Stock Watch List methods
    def get_stock_watchlist(self):
        """Get all stocks in the watch list."""
        session = self.get_session()
        try:
            stocks = session.query(StockWatchList).all()
            return [stock.to_dict() for stock in stocks]
        except Exception as e:
            logger.error(f"Error retrieving stock watchlist: {str(e)}")
            return []
        finally:
            session.close()
    
    def add_stock_to_watchlist(self, symbol, last_price):
        """Add a stock to the watch list."""
        session = self.get_session()
        try:
            # Convert NumPy float to Python float if needed
            if hasattr(last_price, 'item'):
                last_price = float(last_price.item())
            else:
                last_price = float(last_price)
                
            stock = StockWatchList(
                symbol=symbol,
                last_price=last_price,
                added_at=datetime.now()
            )
            session.add(stock)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding stock to watchlist: {str(e)}")
            return False
        finally:
            session.close()
    
    def remove_stock_from_watchlist(self, symbol):
        """Remove a stock from the watch list."""
        session = self.get_session()
        try:
            stock = session.query(StockWatchList).filter_by(symbol=symbol).first()
            if stock:
                session.delete(stock)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error removing stock from watchlist: {str(e)}")
            return False
        finally:
            session.close()
    
    def update_stock_price(self, symbol, last_price):
        """Update the last price for a stock in the watch list."""
        session = self.get_session()
        try:
            # Convert NumPy float to Python float if needed
            if hasattr(last_price, 'item'):
                last_price = float(last_price.item())
            else:
                last_price = float(last_price)
                
            stock = session.query(StockWatchList).filter_by(symbol=symbol).first()
            if stock:
                stock.last_price = last_price
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating stock price: {str(e)}")
            return False
        finally:
            session.close()
    
    def clear_watchlist(self):
        """Clear all stocks from the watch list."""
        session = self.get_session()
        try:
            session.query(StockWatchList).delete()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error clearing watchlist: {str(e)}")
            return False
        finally:
            session.close()
    
    # Trading History methods
    def get_trading_history(self):
        """Get all trading history records."""
        session = self.get_session()
        try:
            history = session.query(TradingHistory).order_by(TradingHistory.timestamp).all()
            records = [record.to_dict() for record in history]
            
            # Convert to DataFrame for consistency with current app
            if records:
                df = pd.DataFrame(records)
                df.rename(columns={
                    'symbol': 'Stock',
                    'action': 'Action',
                    'price': 'Price',
                    'quantity': 'Quantity',
                    'pnl': 'P/L',
                    'reason': 'Reason',
                    'timestamp': 'Timestamp'
                }, inplace=True)
                return df
            else:
                return pd.DataFrame(
                    columns=['Timestamp', 'Stock', 'Action', 'Price', 'Quantity', 'P/L', 'Reason']
                )
        except Exception as e:
            logger.error(f"Error retrieving trading history: {str(e)}")
            return pd.DataFrame(
                columns=['Timestamp', 'Stock', 'Action', 'Price', 'Quantity', 'P/L', 'Reason']
            )
        finally:
            session.close()
    
    def add_trading_record(self, symbol, action, price, quantity, pnl, reason):
        """Add a new trading record to history."""
        session = self.get_session()
        try:
            # Convert NumPy values to Python types if needed
            if hasattr(price, 'item'):
                price = float(price.item())
            else:
                price = float(price)
                
            if hasattr(quantity, 'item'):
                quantity = int(quantity.item())
            else:
                quantity = int(quantity)
                
            if hasattr(pnl, 'item'):
                pnl = float(pnl.item())
            else:
                pnl = float(pnl) if pnl is not None else None
                
            record = TradingHistory(
                symbol=symbol,
                action=action,
                price=price,
                quantity=quantity,
                pnl=pnl,
                reason=reason,
                timestamp=datetime.now()
            )
            session.add(record)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding trading record: {str(e)}")
            return False
        finally:
            session.close()
    
    # Account Settings methods
    def get_account_settings(self):
        """Get account settings."""
        session = self.get_session()
        try:
            settings = session.query(AccountSettings).first()
            if not settings:
                # Create default settings if none exist
                settings = AccountSettings()
                session.add(settings)
                session.commit()
            return settings.to_dict()
        except Exception as e:
            logger.error(f"Error retrieving account settings: {str(e)}")
            return {
                "initial_balance": 10000.0,
                "current_balance": 10000.0,
                "take_profit_pct": 2.0,
                "stop_loss_pct": 1.0,
                "position_size_pct": 10.0
            }
        finally:
            session.close()
    
    def update_account_settings(self, initial_balance=None, current_balance=None, 
                               take_profit_pct=None, stop_loss_pct=None, position_size_pct=None):
        """Update account settings."""
        session = self.get_session()
        try:
            settings = session.query(AccountSettings).first()
            if not settings:
                settings = AccountSettings()
                session.add(settings)
            
            # Update only provided fields
            if initial_balance is not None:
                # Convert NumPy float to Python float if needed
                if hasattr(initial_balance, 'item'):
                    initial_balance = float(initial_balance.item())
                else:
                    initial_balance = float(initial_balance)
                settings.initial_balance = initial_balance
                
            if current_balance is not None:
                # Convert NumPy float to Python float if needed
                if hasattr(current_balance, 'item'):
                    current_balance = float(current_balance.item())
                else:
                    current_balance = float(current_balance)
                settings.current_balance = current_balance
                
            if take_profit_pct is not None:
                # Convert NumPy float to Python float if needed
                if hasattr(take_profit_pct, 'item'):
                    take_profit_pct = float(take_profit_pct.item())
                else:
                    take_profit_pct = float(take_profit_pct)
                settings.take_profit_pct = take_profit_pct
                
            if stop_loss_pct is not None:
                # Convert NumPy float to Python float if needed
                if hasattr(stop_loss_pct, 'item'):
                    stop_loss_pct = float(stop_loss_pct.item())
                else:
                    stop_loss_pct = float(stop_loss_pct)
                settings.stop_loss_pct = stop_loss_pct
                
            if position_size_pct is not None:
                # Convert NumPy float to Python float if needed
                if hasattr(position_size_pct, 'item'):
                    position_size_pct = float(position_size_pct.item())
                else:
                    position_size_pct = float(position_size_pct)
                settings.position_size_pct = position_size_pct
            
            settings.last_updated = datetime.now()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating account settings: {str(e)}")
            return False
        finally:
            session.close()
    
    # Current Position methods
    def get_current_position(self):
        """Get the current position if one exists."""
        session = self.get_session()
        try:
            position = session.query(CurrentPosition).first()
            return position.to_dict() if position else None
        except Exception as e:
            logger.error(f"Error retrieving current position: {str(e)}")
            return None
        finally:
            session.close()
    
    def set_current_position(self, symbol, entry_price, quantity, position_size):
        """Set the current position (replacing any existing one)."""
        session = self.get_session()
        try:
            # First clear any existing positions
            session.query(CurrentPosition).delete()
            
            # Convert NumPy values to Python types if needed
            if hasattr(entry_price, 'item'):
                entry_price = float(entry_price.item())
            else:
                entry_price = float(entry_price)
                
            if hasattr(position_size, 'item'):
                position_size = float(position_size.item())
            else:
                position_size = float(position_size)
                
            if hasattr(quantity, 'item'):
                quantity = int(quantity.item())
            else:
                quantity = int(quantity)
            
            # Then add the new position
            position = CurrentPosition(
                symbol=symbol,
                entry_price=entry_price,
                quantity=quantity,
                position_size=position_size,
                entry_time=datetime.now(),
                position_type="short"
            )
            session.add(position)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error setting current position: {str(e)}")
            return False
        finally:
            session.close()
    
    def clear_current_position(self):
        """Clear the current position."""
        session = self.get_session()
        try:
            session.query(CurrentPosition).delete()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error clearing current position: {str(e)}")
            return False
        finally:
            session.close()