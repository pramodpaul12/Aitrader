import datetime
import pytz
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def is_asx_trading_hours():
    """
    Check if the current time is within ASX trading hours.
    
    Returns:
        bool: True if current time is within ASX trading hours, False otherwise
    """
    # ASX trading hours: 10:00 AM to 4:00 PM Sydney time, Monday to Friday
    sydney_tz = pytz.timezone('Australia/Sydney')
    current_time = datetime.datetime.now(sydney_tz)
    
    # Check if it's a weekday (0 = Monday, 4 = Friday)
    if current_time.weekday() > 4:  # Weekend
        return False
    
    # Check if it's between 10:00 AM and 4:00 PM
    market_open = current_time.replace(hour=10, minute=0, second=0, microsecond=0)
    market_close = current_time.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return market_open <= current_time <= market_close

def get_asx_market_status():
    """
    Get the current status of the ASX market.
    
    Returns:
        tuple: (status, color, message)
    """
    sydney_tz = pytz.timezone('Australia/Sydney')
    current_time = datetime.datetime.now(sydney_tz)
    
    # Check if it's a weekday
    is_weekday = current_time.weekday() <= 4
    
    # Market hours
    market_open = current_time.replace(hour=10, minute=0, second=0, microsecond=0)
    market_close = current_time.replace(hour=16, minute=0, second=0, microsecond=0)
    
    if is_weekday and market_open <= current_time <= market_close:
        # Calculate time until market close
        minutes_until_close = (market_close - current_time).total_seconds() / 60
        hours, minutes = divmod(int(minutes_until_close), 60)
        
        if hours > 0:
            time_msg = f"{hours}h {minutes}m until close"
        else:
            time_msg = f"{minutes}m until close"
            
        return "MARKET OPEN", "#1DB954", time_msg
    else:
        # Calculate time until next open
        if not is_weekday:
            # Calculate days until Monday
            days_to_monday = (7 - current_time.weekday()) % 7
            next_open_day = current_time + datetime.timedelta(days=days_to_monday)
        else:
            if current_time < market_open:
                next_open_day = current_time
            else:
                next_open_day = current_time + datetime.timedelta(days=1)
                if next_open_day.weekday() > 4:  # If next day is weekend, move to Monday
                    next_open_day += datetime.timedelta(days=(7 - next_open_day.weekday()))
        
        next_open = next_open_day.replace(hour=10, minute=0, second=0, microsecond=0)
        time_delta = next_open - current_time
        
        days = time_delta.days
        hours, remainder = divmod(time_delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            time_msg = f"Opens in {days}d {hours}h {minutes}m"
        elif hours > 0:
            time_msg = f"Opens in {hours}h {minutes}m"
        else:
            time_msg = f"Opens in {minutes}m"
            
        return "MARKET CLOSED", "#ff4b4b", time_msg

def format_currency(amount):
    """
    Format a number as currency (AUD).
    
    Args:
        amount (float): Amount to format
        
    Returns:
        str: Formatted currency string
    """
    return f"${amount:,.2f}"

def calculate_position_size(account_balance, risk_percentage, stop_loss_percentage, stock_price):
    """
    Calculate position size based on risk parameters.
    
    Args:
        account_balance (float): Current account balance
        risk_percentage (float): Percentage of account willing to risk (e.g., 1.0 for 1%)
        stop_loss_percentage (float): Stop loss percentage (e.g., 2.0 for 2%)
        stock_price (float): Current stock price
        
    Returns:
        int: Number of shares to trade
    """
    # Calculate dollar risk amount
    risk_amount = account_balance * (risk_percentage / 100)
    
    # Calculate per-share risk (stop loss distance)
    per_share_risk = stock_price * (stop_loss_percentage / 100)
    
    # Calculate position size
    if per_share_risk > 0:
        shares = int(risk_amount / per_share_risk)
        return shares
    return 0

def calculate_performance_metrics(trading_history):
    """
    Calculate performance metrics from trading history.
    
    Args:
        trading_history (pandas.DataFrame): Trading history dataframe
        
    Returns:
        dict: Dictionary of performance metrics
    """
    try:
        if trading_history.empty:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_profit': 0,
                'total_loss': 0,
                'profit_factor': 0,
                'average_win': 0,
                'average_loss': 0,
                'largest_win': 0,
                'largest_loss': 0
            }
        
        # Ensure P/L is numeric
        if not pd.api.types.is_numeric_dtype(trading_history['P/L']):
            trading_history['P/L'] = pd.to_numeric(trading_history['P/L'].replace('[\$,]', '', regex=True))
        
        # Filter to only include close positions
        close_trades = trading_history[trading_history['Action'].str.contains('Close')]
        
        # Calculate metrics
        total_trades = len(close_trades)
        winning_trades = len(close_trades[close_trades['P/L'] > 0])
        losing_trades = len(close_trades[close_trades['P/L'] <= 0])
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_profit = close_trades[close_trades['P/L'] > 0]['P/L'].sum()
        total_loss = close_trades[close_trades['P/L'] <= 0]['P/L'].sum()
        
        profit_factor = abs(total_profit / total_loss) if total_loss != 0 else float('inf')
        
        average_win = total_profit / winning_trades if winning_trades > 0 else 0
        average_loss = total_loss / losing_trades if losing_trades > 0 else 0
        
        largest_win = close_trades['P/L'].max()
        largest_loss = close_trades['P/L'].min()
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'total_loss': total_loss,
            'profit_factor': profit_factor,
            'average_win': average_win,
            'average_loss': average_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss
        }
    
    except Exception as e:
        logger.error(f"Error calculating performance metrics: {str(e)}")
        return {
            'error': str(e)
        }
