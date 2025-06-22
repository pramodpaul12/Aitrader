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
from trading_engine import TradingEngine
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

# Custom CSS for better appearance and mobile responsiveness
st.markdown("""
<style>
/* Base styles */
.main-header {
    font-size: clamp(1.8rem, 5vw, 2.5rem); /* Responsive font sizing */
    color: #00b0f0;
    margin-bottom: 0.5rem;
    line-height: 1.2;
}
.sub-header {
    font-size: clamp(0.9rem, 3vw, 1.2rem); /* Responsive font sizing */
    color: #666;
    margin-bottom: 1.5rem;
    line-height: 1.4;
}
.card {
    padding: clamp(0.8rem, 3vw, 1.5rem); /* Responsive padding */
    border-radius: 0.5rem;
    background-color: #f9f9f9;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    margin-bottom: 1rem;
    overflow-x: auto; /* Allow horizontal scrolling for tables on small screens */
}
.status-active {
    color: #0f9d58;
    font-weight: bold;
}
.status-inactive {
    color: #db4437;
    font-weight: bold;
}
.metric-card {
    background-color: #f5f7fa;
    padding: clamp(0.6rem, 2vw, 1rem); /* Responsive padding */
    border-radius: 0.5rem;
    border-left: 4px solid #00b0f0;
    margin-bottom: 1rem;
    width: 100%; /* Full width on small screens */
}
.label {
    font-size: clamp(0.7rem, 2vw, 0.85rem); /* Responsive font sizing */
    color: #666;
}
.value {
    font-size: clamp(1rem, 3vw, 1.2rem); /* Responsive font sizing */
    font-weight: bold;
}

/* Responsive table styles */
table {
    width: 100%;
    border-collapse: collapse;
}
td, th {
    padding: 8px;
    text-align: left;
    vertical-align: top;
}
@media screen and (max-width: 768px) {
    table, tbody, tr, td {
        display: block;
        width: 100%;
    }
    td {
        border: none;
        position: relative;
        padding-left: 8px;
    }
    td:before {
        font-weight: bold;
        display: inline-block;
        margin-right: 8px;
    }
}

/* Responsive button styles */
button {
    white-space: normal !important; /* Allow text wrapping in buttons */
    word-wrap: break-word;
    min-height: 40px;
}

/* Mobile-friendly tab content */
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1rem;
}

/* Responsive chart containers */
.chart-container {
    width: 100%;
    overflow-x: auto;
}

/* Ensure images and SVGs scale properly */
img, svg {
    max-width: 100%;
    height: auto;
}

/* Fix for Streamlit widgets on mobile */
@media screen and (max-width: 768px) {
    .stTextInput, .stSelectbox, .stNumber, .stSlider {
        width: 100% !important;
    }
    
    /* Fix for columns on mobile */
    .row-widget.stButton, .row-widget.stDownloadButton {
        width: 100% !important;
    }
    
    /* Better spacing on mobile */
    .stButton > button {
        margin-bottom: 10px;
    }
}
</style>
""", unsafe_allow_html=True)

# Header section
st.markdown('<div class="main-header">📉 ASX Short Trading System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-driven shorting system with automatic profit-taking and loss-cutting</div>', unsafe_allow_html=True)

# Market status and key metrics with responsive layout
status, color, message = get_asx_market_status()

# Add CSS for responsive metrics grid
st.markdown("""
<style>
.metrics-grid {
    display: grid;
    gap: 10px;
    margin-bottom: 20px;
}

/* Mobile layout: vertical stack */
@media (max-width: 768px) {
    .metrics-grid {
        grid-template-columns: 1fr;
    }
    .metric-card {
        margin-bottom: 10px;
    }
}

/* Tablet layout: 2 columns */
@media (min-width: 769px) and (max-width: 1200px) {
    .metrics-grid {
        grid-template-columns: 1fr 1fr;
    }
    .metric-card:last-child {
        grid-column: span 2;
    }
}

/* Desktop layout: 3 columns */
@media (min-width: 1201px) {
    .metrics-grid {
        grid-template-columns: 1fr 1fr 2fr;
    }
}
</style>
<div class="metrics-grid">
""", unsafe_allow_html=True)

# Market status card
st.markdown(f"""
<div class="metric-card">
    <div class="label">Market Status</div>
    <div class="value" style="color:{color}">{status}</div>
</div>
""", unsafe_allow_html=True)

# Trading status indicator
trading_status = "Active" if st.session_state.trading_active else "Inactive"
status_class = "status-active" if st.session_state.trading_active else "status-inactive"

st.markdown(f"""
<div class="metric-card">
    <div class="label">Trading Status</div>
    <div class="value {status_class}">{trading_status}</div>
</div>
""", unsafe_allow_html=True)

# Account balance card with change
change = st.session_state.account_balance - st.session_state.initial_balance
change_pct = (change / st.session_state.initial_balance) * 100
change_color = "#0f9d58" if change >= 0 else "#db4437"

st.markdown(f"""
<div class="metric-card">
    <div class="label">Account Balance</div>
    <div class="value">${st.session_state.account_balance:,.2f} 
        <span style="color:{change_color}; font-size:0.9rem;">({change_pct:+.2f}%)</span>
    </div>
</div>
</div><!-- Close metrics-grid -->
""", unsafe_allow_html=True)

# Create tabs for different sections of the app
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📋 Watchlist", "⚙️ Settings", "📈 Analysis"])

# Tab 1: Dashboard
with tab1:
    # Add responsive dashboard layout CSS
    st.markdown("""
    <style>
    @media (max-width: 768px) {
        .dashboard-container {
            display: flex;
            flex-direction: column;
        }
        .position-section, .controls-section {
            width: 100%;
        }
    }
    @media (min-width: 769px) {
        .dashboard-container {
            display: flex;
            gap: 20px;
        }
        .position-section {
            flex: 2;
        }
        .controls-section {
            flex: 1;
        }
    }
    
    /* Responsive progress indicator */
    @media (max-width: 480px) {
        .progress-labels {
            flex-direction: column;
            align-items: flex-start;
        }
        .progress-labels > div {
            margin-bottom: 5px;
        }
    }
    @media (min-width: 481px) {
        .progress-labels {
            display: flex;
            justify-content: space-between;
            padding: 0 10px;
        }
    }
    </style>
    <div class="dashboard-container">
        <div class="position-section">
    """, unsafe_allow_html=True)
    
    # Current position section in the first column
    st.markdown("### Current Position")
    
    if st.session_state.current_position:
        position = st.session_state.current_position
        symbol = position['symbol']
        entry_price = position['entry_price']
        quantity = position['quantity']
        position_size = position['position_size']
        entry_time = position['entry_time']
        
        # Get current price
        try:
            current_data = data_service.get_latest_stock_data(symbol)
            current_price = current_data['last_price']
            
            # Calculate P/L
            pnl = (entry_price - current_price) * quantity
            pnl_pct = (pnl / position_size) * 100
            pnl_color = "#0f9d58" if pnl > 0 else "#db4437"
            
            # Default values from DB
            take_profit_pct = account_settings.get('take_profit_pct', 2.0)
            stop_loss_pct = account_settings.get('stop_loss_pct', 1.0)
            
            # Calculate targets
            take_profit_target = entry_price * (1 - take_profit_pct/100)
            stop_loss_target = entry_price * (1 + stop_loss_pct/100)
            
            # Mobile-friendly position card - using divs for better mobile layout
            st.markdown(f"""
            <div class="card">
                <h3>Short {symbol}</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                    <div><b>Entry Price:</b> ${entry_price:.4f}</div>
                    <div><b>Current Price:</b> ${current_price:.4f}</div>
                    <div><b>Quantity:</b> {quantity} shares</div>
                    <div><b>Position Size:</b> ${position_size:.2f}</div>
                    <div><b>P/L:</b> <span style="color:{pnl_color}">${pnl:.2f} ({pnl_pct:.2f}%)</span></div>
                    <div><b>Entry Time:</b> {entry_time}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Progress bar to visualize profit/loss targets
            # Normalize current price to progress bar scale (0-1)
            price_range = stop_loss_target - take_profit_target
            progress_value = (stop_loss_target - current_price) / price_range if price_range > 0 else 0.5
            progress_value = min(max(progress_value, 0), 1)  # Clamp between 0 and 1
            
            st.markdown("#### Position Progress")
            st.progress(progress_value)
            
            # Annotate progress bar with simple text - responsive layout
            st.markdown(f"""
            <div class="progress-labels">
                <div>Take Profit: <b>${take_profit_target:.4f}</b></div>
                <div>Entry: <b>${entry_price:.4f}</b></div>
                <div>Stop Loss: <b>${stop_loss_target:.4f}</b></div>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error retrieving position data: {str(e)}")
    else:
        st.markdown("""
        <div class="card" style="text-align: center; padding: 2rem;">
            <h3 style="color: #666;">No Active Position</h3>
            <p>The system will automatically open a position when it identifies a high-scoring shorting opportunity.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Close position section div and start controls section div
    st.markdown('</div><div class="controls-section">', unsafe_allow_html=True)
    
    # Trading controls section in the second column
    st.markdown("### Trading Controls")
    
    # Create stylish control buttons - now full width on mobile
    start_button = st.button(
        "🚀 Start Trading", 
        type="primary", 
        disabled=st.session_state.trading_active,
        use_container_width=True
    )
    
    stop_button = st.button(
        "⏹️ Stop Trading", 
        type="secondary", 
        disabled=not st.session_state.trading_active,
        use_container_width=True
    )
    
    refresh_button = st.button(
        "🔄 Refresh Data",
        use_container_width=True
    )
    
    # Toggle auto-refresh
    st.checkbox("🔄 Auto-refresh data", value=st.session_state.auto_refresh, 
                key="auto_refresh_toggle", 
                help="Automatically refresh data every minute")
    
    # Handle button actions
    if start_button:
        if not st.session_state.stock_list:
            st.error("Cannot start trading without stocks in your watch list.")
        else:
            st.session_state.trading_active = True
            st.session_state.auto_refresh = True
            st.success("Trading system activated!")
            st.rerun()
            
    if stop_button:
        st.session_state.trading_active = False
        st.session_state.auto_refresh = False
        
        # Close any open positions
        if st.session_state.current_position:
            try:
                trading_engine.close_position(
                    st.session_state.current_position, 
                    "Manual shutdown",
                    current_price=data_service.get_latest_stock_data(
                        st.session_state.current_position['symbol']
                    )['last_price']
                )
            except Exception as e:
                logger.error(f"Error closing position on shutdown: {str(e)}")
        
        st.warning("Trading system deactivated!")
        st.rerun()
        
    if refresh_button:
        st.success("Data refreshed!")
    
    # Close the container divs
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # Trading history section
    st.markdown("### Trading History")
    if len(st.session_state.trading_history) > 0:
        st.dataframe(st.session_state.trading_history, use_container_width=True, height=200)
    else:
        st.info("No trading history available yet.")
    
    # Performance visualization section
    st.markdown("### Performance")
    if len(st.session_state.trading_history) > 0:
        # Create a running balance column
        history_with_balance = st.session_state.trading_history.copy()
        
        # Filter to only include rows with P/L values
        history_with_balance = history_with_balance[history_with_balance['P/L'].notna()]
        
        if len(history_with_balance) > 0:
            # Convert P/L to numeric if it's not already
            if not pd.api.types.is_numeric_dtype(history_with_balance['P/L']):
                history_with_balance['P/L'] = history_with_balance['P/L'].str.replace('$', '').str.replace(',', '').astype(float)
            
            # Calculate running balance
            running_balance = [st.session_state.initial_balance]
            for pl in history_with_balance['P/L']:
                running_balance.append(running_balance[-1] + pl)
            
            # Remove the initial balance for plotting with timestamp
            running_balance = running_balance[1:]
            
            # Add responsive performance layout CSS
            st.markdown("""
            <style>
            @media (max-width: 768px) {
                .performance-container {
                    display: flex;
                    flex-direction: column;
                }
                .metrics-section, .chart-section {
                    width: 100%;
                }
                .metrics-grid {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 10px;
                    margin-bottom: 20px;
                }
            }
            @media (min-width: 769px) {
                .performance-container {
                    display: flex;
                    gap: 20px;
                }
                .metrics-section {
                    flex: 1;
                }
                .chart-section {
                    flex: 3;
                }
            }
            </style>
            <div class="performance-container">
                <div class="metrics-section">
            """, unsafe_allow_html=True)
            
            # Performance metrics
            total_trades = len(history_with_balance)
            winning_trades = len(history_with_balance[history_with_balance['P/L'] > 0])
            losing_trades = total_trades - winning_trades
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            total_profit = history_with_balance[history_with_balance['P/L'] > 0]['P/L'].sum()
            total_loss = history_with_balance[history_with_balance['P/L'] < 0]['P/L'].sum()
            
            st.markdown("""
            <div style="background-color: #f5f7fa; padding: 1rem; border-radius: 0.5rem;">
                <h4 style="margin-top: 0;">Trading Metrics</h4>
                <div class="metrics-grid">
            """, unsafe_allow_html=True)
            
            # Use Streamlit's metric components
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Trades", total_trades)
                st.metric("Total Profit", f"${total_profit:.2f}")
            
            with col2:
                st.metric("Win Rate", f"{win_rate:.1f}%")
                st.metric("Total Loss", f"${total_loss:.2f}")
            
            st.markdown("""
                </div>
            </div>
            </div>
            <div class="chart-section">
            """, unsafe_allow_html=True)
            
            # Create the plot
            fig = go.Figure()
            
            # Add the balance line
            fig.add_trace(go.Scatter(
                x=history_with_balance['Timestamp'],
                y=running_balance,
                mode='lines+markers',
                name='Account Balance',
                line=dict(color='#00b0f0', width=2)
            ))
            
            # Add a horizontal line for initial balance
            fig.add_shape(
                type="line",
                x0=history_with_balance['Timestamp'].iloc[0],
                y0=st.session_state.initial_balance,
                x1=history_with_balance['Timestamp'].iloc[-1],
                y1=st.session_state.initial_balance,
                line=dict(color="red", width=1, dash="dash"),
            )
            
            # Add annotations for significant events
            for i, row in history_with_balance.iterrows():
                if abs(row['P/L']) > (st.session_state.initial_balance * 0.01):  # Significant profit/loss (> 1% of initial)
                    fig.add_annotation(
                        x=row['Timestamp'],
                        y=running_balance[i],
                        text=f"{row['Stock']}: {row['Action']}",
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=1,
                        arrowcolor="black"
                    )
            
            # Update layout
            fig.update_layout(
                title='Account Balance Over Time',
                xaxis_title='Time',
                yaxis_title='Balance (AUD)',
                hovermode='x unified',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=0, r=0, b=0, t=40),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
                
            # Close the chart section div
            st.markdown('</div></div>', unsafe_allow_html=True)
        else:
            st.info("Insufficient trading data for visualization.")
    else:
        st.info("No trading history available for visualization.")

# Tab 2: Watchlist Management
with tab2:
    st.markdown("### Stock Watchlist")
    
    # Add stocks section
    st.markdown("#### Add Stocks")
    
    # Responsive layout for mobile - stack on small screens
    # Use custom CSS to control column sizes based on screen width
    st.markdown("""
    <style>
    @media (max-width: 768px) {
        .stock-entry-form {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .stock-entry-input {
            width: 100%;
        }
        .stock-entry-button {
            width: 100%;
        }
    }
    @media (min-width: 769px) {
        .stock-entry-form {
            display: flex;
            gap: 10px;
        }
        .stock-entry-input {
            flex: 3;
        }
        .stock-entry-button {
            flex: 1;
        }
    }
    </style>
    <div class="stock-entry-form">
        <div class="stock-entry-input">
    """, unsafe_allow_html=True)
    
    new_stock = st.text_input("Enter Stock Symbol (e.g., 'CBA.AX', 'AAPL')")
    
    st.markdown("</div><div class='stock-entry-button'>", unsafe_allow_html=True)
    
    add_stock_button = st.button("Add Stock", type="primary", use_container_width=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Quick add buttons for common stocks with better organization
    st.markdown("#### Quick Add Popular Stocks")
    
    # Create tabs for different categories - these are already responsive
    stock_cat1, stock_cat2, stock_cat3 = st.tabs(["ASX Banking", "ASX Resources", "US Tech"])
    
    # Determine number of columns based on viewport width using CSS and HTML
    st.markdown("""
    <style>
    .stock-button-grid {
        display: grid;
        gap: 8px;
        margin-bottom: 15px;
    }
    @media (max-width: 480px) {
        .stock-button-grid { grid-template-columns: repeat(2, 1fr); }
    }
    @media (min-width: 481px) and (max-width: 768px) {
        .stock-button-grid { grid-template-columns: repeat(3, 1fr); }
    }
    @media (min-width: 769px) {
        .stock-button-grid { grid-template-columns: repeat(4, 1fr); }
    }
    </style>
    """, unsafe_allow_html=True)
    
    with stock_cat1:
        # Create a 2x2 grid for mobile, 4x1 for desktop
        asx_banks = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX"]
        
        # For mobile, we'll use 2 columns
        cols = st.columns([1, 1])
        for i, bank in enumerate(asx_banks):
            with cols[i % 2]:
                if st.button(bank, key=f"bank_{bank}", use_container_width=True):
                    new_stock = bank
                
    with stock_cat2:
        asx_resources = ["BHP.AX", "FMG.AX", "RIO.AX", "NCM.AX"]
        
        cols = st.columns([1, 1])
        for i, resource in enumerate(asx_resources):
            with cols[i % 2]:
                if st.button(resource, key=f"resource_{resource}", use_container_width=True):
                    new_stock = resource
    
    with stock_cat3:
        us_tech = ["AAPL", "MSFT", "GOOGL", "AMZN"]
        
        cols = st.columns([1, 1])
        for i, tech in enumerate(us_tech):
            with cols[i % 2]:
                if st.button(tech, key=f"tech_{tech}", use_container_width=True):
                    new_stock = tech
    
    # Additional small cap stocks
    st.markdown("#### Other Stocks")
    
    # For mobile, we'll use 2 columns for these as well
    other_stocks = ["ZIP.AX", "APT.AX", "TSLA", "VERO"]
    
    cols = st.columns([1, 1])
    for i, stock in enumerate(other_stocks):
        with cols[i % 2]:
            if st.button(stock, key=f"other_{stock}", use_container_width=True):
                new_stock = stock
    
    # Add stock to watch list if provided
    if new_stock or add_stock_button:
        if new_stock:
            try:
                # First get latest data to verify stock exists and get current price
                latest_data = data_service.get_latest_stock_data(new_stock)
                
                if latest_data and 'last_price' in latest_data:
                    # Add to database
                    if db_manager.add_stock_to_watchlist(new_stock, latest_data['last_price']):
                        # Update session state
                        st.session_state.stock_list = db_manager.get_stock_watchlist()
                        st.success(f"Added {new_stock} to watch list at ${latest_data['last_price']:.2f}")
                    else:
                        st.error(f"Failed to add {new_stock} to watch list")
                else:
                    st.error(f"Could not retrieve data for {new_stock}. Please check the symbol.")
            except ValueError as e:
                st.warning(str(e))  # Stock already in watch list
            except Exception as e:
                logger.error(f"Error adding stock {new_stock}: {str(e)}")
                st.error(f"Error adding stock {new_stock}: {str(e)}")
    
    # Show current watch list with better styling
    st.markdown("#### Current Watchlist")
    if st.session_state.stock_list:
        # Create a DataFrame for better display
        watch_list_df = pd.DataFrame(st.session_state.stock_list)
        
        # Format the last price as currency
        if 'last_price' in watch_list_df.columns:
            watch_list_df['last_price'] = watch_list_df['last_price'].apply(lambda x: f"${x:.2f}")
            
        # Rename columns for display
        watch_list_df = watch_list_df.rename(columns={
            'symbol': 'Symbol',
            'last_price': 'Last Price',
            'added_at': 'Added'
        })
        
        # Sort by symbol
        watch_list_df = watch_list_df.sort_values('Symbol')
        
        # Create a DataFrame display with options
        col1, col2 = st.columns([3, 1])
        with col1:
            st.dataframe(watch_list_df, use_container_width=True)
        with col2:
            if st.button("🗑️ Clear All Stocks", type="secondary", use_container_width=True):
                if db_manager.clear_watchlist():
                    st.session_state.stock_list = []
                    st.success("Watchlist cleared successfully.")
                    st.rerun()
        
        # Display individual remove buttons
        st.markdown("#### Remove Individual Stocks")
        
        # Create 4 columns layout for stock removal buttons
        cols = st.columns(4)
        for i, row in enumerate(watch_list_df.iterrows()):
            col_idx = i % 4
            with cols[col_idx]:
                if st.button(f"❌ {row[1]['Symbol']}", key=f"remove_{row[1]['Symbol']}"):
                    if db_manager.remove_stock_from_watchlist(row[1]['Symbol']):
                        st.session_state.stock_list = db_manager.get_stock_watchlist()
                        st.success(f"Removed {row[1]['Symbol']} from watchlist.")
                        st.rerun()
    else:
        st.info("No stocks in watch list. Add some using the options above.")

# Tab 3: Settings
with tab3:
    st.markdown("### Trading Settings")
    
    # Add responsive styling for settings layout
    st.markdown("""
    <style>
    @media (max-width: 768px) {
        .settings-container {
            display: flex;
            flex-direction: column;
        }
        .settings-section {
            width: 100%;
            margin-bottom: 2rem;
        }
    }
    @media (min-width: 769px) {
        .settings-container {
            display: flex;
            gap: 20px;
        }
        .settings-section {
            flex: 1;
        }
    }
    .settings-card {
        background-color: #f9f9f9;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    </style>
    <div class="settings-container">
        <div class="settings-section">
    """, unsafe_allow_html=True)
    
    # Trading Parameters Section
    st.markdown("#### Trading Parameters")
    
    # Default values from DB
    take_profit_pct = account_settings.get('take_profit_pct', 2.0)
    stop_loss_pct = account_settings.get('stop_loss_pct', 1.0)
    position_size_pct = account_settings.get('position_size_pct', 10.0)
    
    with st.container():
        st.markdown('<div class="settings-card">', unsafe_allow_html=True)
        
        # Use number inputs for more precise control
        take_profit_pct = st.number_input(
            "Take Profit (%)", 
            min_value=0.5, 
            max_value=10.0, 
            value=take_profit_pct,
            step=0.1,
            help="Percentage decrease in price at which to take profit"
        )
        
        stop_loss_pct = st.number_input(
            "Stop Loss (%)", 
            min_value=0.5, 
            max_value=5.0, 
            value=stop_loss_pct,
            step=0.1,
            help="Percentage increase in price at which to cut losses"
        )
        
        position_size_pct = st.number_input(
            "Position Size (%)", 
            min_value=1.0, 
            max_value=50.0, 
            value=position_size_pct,
            step=1.0,
            help="Percentage of account balance to use for each position"
        )
        
        # Save settings button
        if st.button("Save Trading Parameters", type="primary", use_container_width=True):
            db_manager.update_account_settings(
                take_profit_pct=take_profit_pct,
                stop_loss_pct=stop_loss_pct,
                position_size_pct=position_size_pct
            )
            st.success("Trading parameters saved successfully!")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Close the first section and start second section for account settings
    st.markdown('</div><div class="settings-section">', unsafe_allow_html=True)
    
    st.markdown("#### Account Settings")
    
    # Initial balance adjustment card
    with st.container():
        st.markdown('<div class="settings-card">', unsafe_allow_html=True)
        st.markdown("##### Initial Balance")
        
        new_initial_balance = st.number_input(
            "Initial Account Balance ($)",
            min_value=100.0,
            max_value=1000000.0,
            value=st.session_state.initial_balance,
            step=1000.0,
            help="Change the initial balance for the simulation"
        )
        
        # Reset account button
        if st.button("Reset Account", type="secondary", use_container_width=True):
            if db_manager.update_account_settings(
                initial_balance=new_initial_balance,
                current_balance=new_initial_balance
            ):
                st.session_state.initial_balance = new_initial_balance
                st.session_state.account_balance = new_initial_balance
                st.success(f"Account reset to ${new_initial_balance:,.2f}")
                
                # Also clear trading history
                if st.session_state.trading_history is not None and len(st.session_state.trading_history) > 0:
                    # Clear trading history (Note: in a real app, you'd add a proper method to clear history)
                    st.warning("Note: Trading history would be cleared in a full implementation.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Trading cycle settings card
    with st.container():
        st.markdown('<div class="settings-card">', unsafe_allow_html=True)
        st.markdown("##### Trading Cycles")
        
        # Time between trading cycles
        hours = st.select_slider(
            "Hours Between Trading Cycles",
            options=[0.5, 1, 2, 3, 4, 6, 12, 24],
            value=1.0,
            help="Time between evaluating new trading opportunities"
        )
        
        if st.button("Update Trading Cycle", type="secondary", use_container_width=True):
            # Convert hours to seconds
            st.session_state.cycle_interval = int(hours * 3600)
            st.success(f"Trading cycle updated to {hours} hour{'s' if hours != 1 else ''}")
        
        # Explanation of trading cycles
        st.info("""
        The trading cycle determines how often the system evaluates your watchlist to find new shorting opportunities. 
        At the end of each cycle, any open positions are closed and a new stock is selected.
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Close the container divs
    st.markdown('</div></div>', unsafe_allow_html=True)

# Tab 4: Analysis
with tab4:
    st.markdown("### Stock Analysis")
    
    # Select a stock to analyze
    if st.session_state.stock_list:
        symbols = [stock['symbol'] for stock in st.session_state.stock_list]
        selected_stock = st.selectbox("Select a stock to analyze", symbols)
        
        if selected_stock:
            try:
                # Get historical data
                st.markdown(f"#### Analysis for {selected_stock}")
                
                with st.spinner("Fetching stock data..."):
                    # Get data for multiple timeframes
                    data_1d = data_service.get_stock_historical_data(selected_stock, period="1d", interval="1m")
                    data_1mo = data_service.get_stock_historical_data(selected_stock, period="1mo", interval="1d")
                
                # Create tabs for different analysis views
                analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs(["Short-Term Analysis", "Long-Term Trend", "Technical Indicators"])
                
                with analysis_tab1:
                    # Get recommendation
                    recommendation = analyzer.get_recommendation(selected_stock, data_1d)
                    
                    # Display recommendation with nice formatting
                    rec_color = {
                        'STRONG SHORT': 'green',
                        'SHORT': 'lightgreen',
                        'NEUTRAL': 'gray',
                        'LONG': 'orange',
                        'STRONG LONG': 'red'  # Red is bad for shorting
                    }.get(recommendation['recommendation'], 'gray')
                    
                    score = recommendation['score']
                    
                    st.markdown(f"""
                    <div style="background-color: #f5f7fa; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                        <h4 style="margin-top: 0;">Shorting Recommendation</h4>
                        <div style="font-size: 1.8rem; font-weight: bold; color: {rec_color};">
                            {recommendation['recommendation']}
                        </div>
                        <div style="margin-top: 0.5rem;">
                            <b>Score:</b> {score}/100
                            <div style="background-color: #e0e0e0; height: 10px; border-radius: 5px; margin-top: 5px;">
                                <div style="width: {score}%; background-color: {rec_color}; height: 10px; border-radius: 5px;"></div>
                            </div>
                        </div>
                        <div style="margin-top: 1rem;">
                            <b>Factors:</b>
                            <ul>
                    """, unsafe_allow_html=True)
                    
                    # List the factors that went into the recommendation
                    for factor, value in recommendation.get('factors', {}).items():
                        st.markdown(f"<li>{factor}: {value}</li>", unsafe_allow_html=True)
                    
                    st.markdown("""
                            </ul>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Price chart for today
                    if data_1d is not None and not data_1d.empty:
                        st.markdown("#### Today's Price Movement")
                        
                        fig = go.Figure()
                        
                        # Add candlestick chart
                        fig.add_trace(go.Candlestick(
                            x=data_1d.index,
                            open=data_1d['Open'],
                            high=data_1d['High'],
                            low=data_1d['Low'],
                            close=data_1d['Close'],
                            name='Price'
                        ))
                        
                        # Update layout
                        fig.update_layout(
                            title=f'{selected_stock} - 1 Day Price Movement',
                            xaxis_title='Time',
                            yaxis_title='Price',
                            xaxis_rangeslider_visible=False,
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("No intraday data available for this stock.")
                
                with analysis_tab2:
                    # Long-term trend analysis
                    if data_1mo is not None and not data_1mo.empty:
                        st.markdown("#### Monthly Price Trend")
                        
                        fig = go.Figure()
                        
                        # Add candlestick chart
                        fig.add_trace(go.Candlestick(
                            x=data_1mo.index,
                            open=data_1mo['Open'],
                            high=data_1mo['High'],
                            low=data_1mo['Low'],
                            close=data_1mo['Close'],
                            name='Price'
                        ))
                        
                        # Add a trendline if enough data
                        if len(data_1mo) > 5:
                            # Simple 20-day moving average
                            data_1mo['MA20'] = data_1mo['Close'].rolling(window=20).mean()
                            
                            fig.add_trace(go.Scatter(
                                x=data_1mo.index,
                                y=data_1mo['MA20'],
                                mode='lines',
                                name='20-Day MA',
                                line=dict(color='blue', width=1)
                            ))
                        
                        # Update layout
                        fig.update_layout(
                            title=f'{selected_stock} - 1 Month Price Trend',
                            xaxis_title='Date',
                            yaxis_title='Price',
                            xaxis_rangeslider_visible=False,
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Show key statistics
                        price_change = (data_1mo['Close'].iloc[-1] - data_1mo['Close'].iloc[0]) / data_1mo['Close'].iloc[0] * 100
                        price_color = "red" if price_change > 0 else "green"  # Red is bad for shorting, green is good
                        
                        highest = data_1mo['High'].max()
                        lowest = data_1mo['Low'].min()
                        current = data_1mo['Close'].iloc[-1]
                        
                        # Responsive statistics display using CSS
                        css = """
<style>
/* Stats container becomes vertical on mobile */
@media (max-width: 768px) {
    .stats-container {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .stat-card {
        width: 100% !important;
    }
}
@media (min-width: 769px) {
    .stats-container {
        display: flex;
        justify-content: space-between;
        margin-top: 1rem;
        gap: 15px;
    }
    .stat-card {
        width: 33%;
    }
}
.stat-card {
    background-color: #f5f7fa;
    padding: 1rem;
    border-radius: 0.5rem;
}
</style>
"""
                        st.markdown(css, unsafe_allow_html=True)
                        
                        # Create the stats cards with the prepared CSS
                        stats_html = f"""
<div class="stats-container">
    <div class="stat-card">
        <div style="font-size: 0.9rem; color: #666;">Price Change (1 Month)</div>
        <div style="font-size: 1.2rem; font-weight: bold; color: {price_color};">{price_change:.2f}%</div>
    </div>
    <div class="stat-card">
        <div style="font-size: 0.9rem; color: #666;">Highest Price</div>
        <div style="font-size: 1.2rem; font-weight: bold;">${highest:.2f}</div>
    </div>
    <div class="stat-card">
        <div style="font-size: 0.9rem; color: #666;">Lowest Price</div>
        <div style="font-size: 1.2rem; font-weight: bold;">${lowest:.2f}</div>
    </div>
</div>
"""
                        st.markdown(stats_html, unsafe_allow_html=True)
                    else:
                        st.warning("No monthly data available for this stock.")
                
                with analysis_tab3:
                    # Technical indicators
                    if data_1d is not None and not data_1d.empty:
                        # Calculate indicators
                        data_with_indicators = analyzer._calculate_indicators(data_1d.copy())
                        
                        # Pick some interesting indicators to display
                        indicators = ['RSI', 'MACD', 'MACD_Signal', 'Upper_Band', 'Lower_Band']
                        available_indicators = [ind for ind in indicators if ind in data_with_indicators.columns]
                        
                        if available_indicators:
                            st.markdown("#### Technical Indicators")
                            
                            selected_indicator = st.selectbox(
                                "Select Technical Indicator", 
                                available_indicators
                            )
                            
                            if selected_indicator:
                                # Create plot for the selected indicator
                                fig = go.Figure()
                                
                                # Plot close price
                                fig.add_trace(go.Scatter(
                                    x=data_with_indicators.index,
                                    y=data_with_indicators['Close'],
                                    mode='lines',
                                    name='Close Price',
                                    line=dict(color='blue', width=1)
                                ))
                                
                                # Add the indicator
                                fig.add_trace(go.Scatter(
                                    x=data_with_indicators.index,
                                    y=data_with_indicators[selected_indicator],
                                    mode='lines',
                                    name=selected_indicator,
                                    line=dict(color='red', width=1)
                                ))
                                
                                # Add secondary y-axis for the indicator
                                fig.update_layout(
                                    title=f'{selected_stock} - {selected_indicator}',
                                    xaxis_title='Time',
                                    yaxis_title='Price',
                                    yaxis2=dict(
                                        title=selected_indicator,
                                        overlaying='y',
                                        side='right'
                                    ),
                                    height=400
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Explanation of the indicator
                                explanations = {
                                    'RSI': """
                                    **Relative Strength Index (RSI)** measures the speed and magnitude of price movements.
                                    - Above 70: Potentially overbought (good for shorting)
                                    - Below 30: Potentially oversold (poor for shorting)
                                    """,
                                    'MACD': """
                                    **Moving Average Convergence Divergence (MACD)** shows the relationship between two moving averages.
                                    - MACD crossing below signal line: Bearish signal (good for shorting)
                                    - MACD crossing above signal line: Bullish signal (poor for shorting)
                                    """,
                                    'Upper_Band': """
                                    **Bollinger Upper Band** is 2 standard deviations above the 20-period moving average.
                                    - Price near or above the upper band may indicate overbought conditions (good for shorting)
                                    """,
                                    'Lower_Band': """
                                    **Bollinger Lower Band** is 2 standard deviations below the 20-period moving average.
                                    - Price near or below the lower band may indicate oversold conditions (poor for shorting)
                                    """
                                }
                                
                                if selected_indicator in explanations:
                                    st.markdown(explanations[selected_indicator])
                                
                                # Current indicator value
                                current_value = data_with_indicators[selected_indicator].iloc[-1]
                                st.markdown(f"**Current {selected_indicator} Value:** {current_value:.2f}")
                        else:
                            st.warning("No technical indicators available for this stock.")
                    else:
                        st.warning("Insufficient data to calculate technical indicators.")
            except Exception as e:
                st.error(f"Error analyzing {selected_stock}: {str(e)}")
    else:
        st.info("Add stocks to your watchlist to analyze them.")

# Hidden trading logic (runs in the background)
if st.session_state.trading_active and st.session_state.auto_refresh:
    # Record current time for multiple refresh checks
    current_time = datetime.now()
    
    # Check if it's time for a refresh (every minute)
    time_since_refresh = (current_time - st.session_state.last_refresh).total_seconds()
    if time_since_refresh >= st.session_state.refresh_interval:
        st.session_state.last_refresh = current_time
        
        # Update watchlist prices
        for stock in st.session_state.stock_list:
            try:
                latest_data = data_service.get_latest_stock_data(stock['symbol'])
                stock['last_price'] = latest_data['last_price']
                
                # Update in database
                db_manager.update_stock_price(stock['symbol'], latest_data['last_price'])
            except Exception as e:
                logger.error(f"Error updating price for {stock['symbol']}: {str(e)}")
        
        # Sync account settings with database
        db_manager.update_account_settings(
            current_balance=st.session_state.account_balance,
            take_profit_pct=take_profit_pct,
            stop_loss_pct=stop_loss_pct,
            position_size_pct=position_size_pct
        )
    
    # Check if we're in trading hours
    if is_asx_trading_hours():
        with st.spinner("Processing trading logic..."):
            try:
                # Check if it's time for a cycle (hourly trading cycles)
                time_since_cycle = (current_time - st.session_state.last_cycle).total_seconds()
                
                # Check if we have an open position
                if st.session_state.current_position:
                    position = st.session_state.current_position
                    current_price = data_service.get_latest_stock_data(position['symbol'])['last_price']
                    
                    # Get current trading parameters from account settings
                    account_settings = db_manager.get_account_settings()
                    take_profit_pct = account_settings.get('take_profit_pct', 2.0)
                    stop_loss_pct = account_settings.get('stop_loss_pct', 1.0)
                    
                    # For short positions, check if price decreased enough for profit or increased too much for loss
                    entry_price = position['entry_price']
                    
                    # Check take profit condition (price decreased)
                    take_profit_target = entry_price * (1 - take_profit_pct/100)
                    if current_price <= take_profit_target:
                        pnl = trading_engine.close_position(position, "Take profit", current_price)
                        st.success(f"Take profit executed for {position['symbol']} at ${current_price:.2f}, P/L: ${pnl:.2f}")
                        
                        # After taking profit, move to the next stock in the list
                        time_since_cycle = st.session_state.cycle_interval  # Force next cycle to start
                        
                    # Check stop loss condition (price increased)
                    stop_loss_target = entry_price * (1 + stop_loss_pct/100)
                    if current_price >= stop_loss_target:
                        pnl = trading_engine.close_position(position, "Stop loss", current_price)
                        st.warning(f"Stop loss executed for {position['symbol']} at ${current_price:.2f}, P/L: ${pnl:.2f}")
                        
                        # After cutting losses, move to the next stock in the list
                        time_since_cycle = st.session_state.cycle_interval  # Force next cycle to start
                    
                    # Check if it's time for a cycle change and we're still in the same position
                    elif time_since_cycle >= st.session_state.cycle_interval and st.session_state.current_position:
                        # Close current position to rotate to next stock
                        pnl = trading_engine.close_position(position, "End of cycle rotation", current_price)
                        st.info(f"Cycle ended for {position['symbol']} at ${current_price:.2f}, P/L: ${pnl:.2f}")
                        st.session_state.last_cycle = current_time
                
                # If no open position and it's time for a new cycle, find a new stock to short
                elif (time_since_cycle >= st.session_state.cycle_interval or not st.session_state.current_position) and st.session_state.stock_list:
                    st.session_state.last_cycle = current_time
                    
                    # Find the next stock with the highest shorting score
                    best_stock = None
                    best_score = 0
                    
                    for stock in st.session_state.stock_list:
                        symbol = stock['symbol']
                        try:
                            # Get historical data
                            data = data_service.get_stock_historical_data(symbol, period="1d", interval="1m")
                            
                            # Get recommendation
                            recommendation = analyzer.get_recommendation(symbol, data)
                            
                            # Check if it's a good shorting opportunity
                            if recommendation['recommendation'] in ['SHORT', 'STRONG SHORT'] and recommendation['score'] > best_score:
                                best_stock = stock
                                best_score = recommendation['score']
                                
                        except Exception as e:
                            logger.error(f"Error analyzing {symbol}: {str(e)}")
                    
                    # If we found a good stock to short, open a position
                    if best_stock and best_score >= 60:  # Only short if score is at least 60
                        symbol = best_stock['symbol']
                        current_price = data_service.get_latest_stock_data(symbol)['last_price']
                        
                        # Get position size from account settings
                        account_settings = db_manager.get_account_settings()
                        position_size_pct = account_settings.get('position_size_pct', 10.0)
                        
                        # Calculate position size
                        position_size = st.session_state.account_balance * (position_size_pct / 100)
                        
                        # Open position
                        try:
                            position = trading_engine.open_position(symbol, position_size, current_price)
                            st.success(f"Opened short position for {symbol} at ${current_price:.2f}")
                        except Exception as e:
                            logger.error(f"Error opening position: {str(e)}")
                            st.error(f"Error opening position: {str(e)}")
                    else:
                        logger.info("No suitable shorting opportunities found this cycle")
                        with tab1:
                            st.info("No suitable shorting opportunities found in this cycle. Will check again soon.")
            
            except Exception as e:
                logger.error(f"Error in trading logic: {str(e)}")
                st.error(f"Error in trading logic: {str(e)}")
    else:
        # If outside trading hours and we have an open position, close it
        if st.session_state.current_position:
            try:
                symbol = st.session_state.current_position['symbol']
                current_price = data_service.get_latest_stock_data(symbol)['last_price']
                pnl = trading_engine.close_position(
                    st.session_state.current_position, 
                    "Market closed",
                    current_price=current_price
                )
                st.warning(f"Closed position for {symbol} because market is closed. P/L: ${pnl:.2f}")
            except Exception as e:
                logger.error(f"Error closing position on market close: {str(e)}")
        
        # Display warning in the first tab
        with tab1:
            st.warning("Trading paused - outside ASX trading hours")

# Auto-refresh functionality (more frequent than cycle interval)
if st.session_state.auto_refresh:
    # We'll refresh at our set interval rather than a fixed 60 seconds
    time.sleep(min(60, st.session_state.refresh_interval))  # Use the smaller of 60 sec or our refresh interval
    st.rerun()