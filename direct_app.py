import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import logging
from datetime import datetime, timedelta
import pytz

# Import custom modules
from data_service import DataService
from stock_analyzer import StockAnalyzer
from trading_engine_direct import TradingEngine  # Use our direct copy
from db_manager import DatabaseManager
from utils import is_asx_trading_hours, get_asx_market_status, format_currency, calculate_performance_metrics
from logger_config import setup_logger

# Setup logging
logger = setup_logger()

# Initialize services
data_service = DataService()
db_manager = DatabaseManager()
analyzer = StockAnalyzer()
trading_engine = TradingEngine(data_service, analyzer)

# Set page config
st.set_page_config(
    page_title="ASX Short Trading System",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for persistence across reruns
if 'stock_list' not in st.session_state:
    st.session_state.stock_list = db_manager.get_stock_watchlist()

if 'trading_history' not in st.session_state:
    st.session_state.trading_history = db_manager.get_trading_history()
    
if 'current_position' not in st.session_state:
    st.session_state.current_position = db_manager.get_current_position()
    
if 'trading_active' not in st.session_state:
    st.session_state.trading_active = False
    
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
    
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
    
if 'last_cycle' not in st.session_state:
    st.session_state.last_cycle = datetime.now()
    
if 'refresh_interval' not in st.session_state:
    st.session_state.refresh_interval = 60  # 60 seconds refresh interval
    
if 'cycle_interval' not in st.session_state:
    st.session_state.cycle_interval = 3600  # 1 hour trading cycle

# Get account settings from DB
account_settings = db_manager.get_account_settings()

if 'initial_balance' not in st.session_state:
    st.session_state.initial_balance = account_settings.get('initial_balance', 10000.0)
    
if 'account_balance' not in st.session_state:
    st.session_state.account_balance = account_settings.get('current_balance', 10000.0)

# This is just a test app to verify we can import the trading engine successfully
st.title("Import Test Success")
st.success("Successfully imported TradingEngine from the direct file!")