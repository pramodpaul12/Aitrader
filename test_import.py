try:
    from trading_engine import TradingEngine
    print("Successfully imported TradingEngine")
except ImportError as e:
    print(f"Import error: {e}")
    
# Print module information
import sys
print(f"Python path: {sys.path}")
print(f"Module cache: {list(sys.modules.keys())}")