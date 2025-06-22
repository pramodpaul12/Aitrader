print("Starting test")
try:
    import trading_engine
    print(f"Module attributes: {dir(trading_engine)}")
    if hasattr(trading_engine, 'TradingEngine'):
        print("TradingEngine class exists in the module")
    else:
        print("TradingEngine class does NOT exist in the module")
except Exception as e:
    print(f"Error: {e}")
print("Test completed")