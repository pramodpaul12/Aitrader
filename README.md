# ASX Trading System

An advanced day trading system for shorting ASX stocks, featuring intelligent profit-taking and loss-cutting mechanisms with enhanced UI and user experience.

## Overview

This application is designed to automate day trading on the Australian Stock Exchange (ASX) with a focus on short selling. The system systematically shorts stocks from a user-provided watchlist when the market opens, takes profit when available, cuts losses immediately, and moves to other stocks in the list. 

The application operates in multiple trading cycles throughout the day to maximize opportunities while ensuring all positions are closed before the market closes.

## Features

- **Intelligent Trading Logic**: Automated shorting with configurable take-profit and stop-loss mechanisms
- **Real-time Data**: Integration with market data providers for real-time price information
- **Technical Analysis**: Built-in technical indicators to evaluate shorting opportunities
- **Brokerage Integration**: Support for connecting to trading platforms via APIs
- **Performance Tracking**: Detailed transaction history and performance metrics
- **Mobile-Responsive UI**: Modern interface accessible on all devices
- **Simulation Mode**: Practice with virtual money before committing real funds

## Technology Stack

- **Frontend**: Streamlit for interactive UI
- **Data Processing**: Pandas and NumPy for analysis
- **Visualization**: Plotly for charts and metrics
- **Database**: PostgreSQL for data persistence
- **API Integration**: Alpaca Markets API for brokerage services

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/asx-trading-system.git
cd asx-trading-system
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Create a .env file with the following variables
ALPACA_API_KEY=your_api_key
ALPACA_API_SECRET=your_api_secret
ENABLE_REAL_TRADING=false
USE_TRADING_SANDBOX=true
BROKERAGE_TYPE=alpaca
```

4. Run the application:
```bash
streamlit run app.py
```

## Usage

1. **Configure Trading Parameters**: Set your risk preferences, position size, and trading frequency.
2. **Manage Watchlist**: Add or remove ASX stocks from your watchlist.
3. **Monitor Dashboard**: View current positions, historical performance, and market status.
4. **Analyze Stocks**: Use built-in technical analysis tools to evaluate opportunities.
5. **Trade**: Enable automated trading or manually control positions.

## Structure

- `app.py`: Main Streamlit application with UI components
- `trading_engine.py`: Core trading logic and execution
- `data_service.py`: Market data retrieval and processing
- `stock_analyzer.py`: Technical analysis and trade signal generation
- `db_manager.py`: Database operations
- `brokerage_connector.py`: API integration with trading platforms
- `asx_trading_service.py`: ASX-specific trading operations

## Configuration

The system can be configured through the UI or by modifying `app.py`. Key configurable parameters include:

- Initial account balance
- Position size percentage
- Take profit percentage
- Stop loss percentage
- Trading cycle interval
- Market hours
- Watchlist management

## Disclaimer

This software is for educational and informational purposes only. Trading securities involves risk, and past performance is not indicative of future results. Users are advised to use caution and consult with a financial advisor before making investment decisions.

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.