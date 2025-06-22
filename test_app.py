import streamlit as st

st.title("Trading Engine Import Test")

st.write("Attempting to import TradingEngine...")

try:
    import trading_engine
    st.write("Successfully imported trading_engine module")
    
    st.write(f"Module attributes: {dir(trading_engine)}")
    
    if hasattr(trading_engine, 'TradingEngine'):
        st.success("TradingEngine class exists in the module")
    else:
        st.error("TradingEngine class does NOT exist in the module")
        
    # Try direct import
    try:
        from trading_engine import TradingEngine
        st.success("Successfully imported TradingEngine class directly")
    except ImportError as e:
        st.error(f"Could not import TradingEngine directly: {e}")
        
except Exception as e:
    st.error(f"Error importing module: {e}")
    
st.write("Test completed")