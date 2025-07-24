# main.py

import streamlit as st
import pytz
from datetime import datetime
from realtime_forecast import fetch_candle_data, analyze_signal

# Set your TwelveData API key here
API_KEY = "899db61d39f640c5bbffc54fab5785e7"

# Timezone for IST
IST = pytz.timezone("Asia/Kolkata")

st.title("📈 AI Forex Signal Predictor (Real-Time)")
st.markdown("Select a currency pair and timeframe. Get real-time AI signal.")

symbol = st.selectbox("Choose Currency Pair", [
    "EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CHF", "USD/CAD", "NZD/USD", "EUR/JPY", "GBP/JPY"
])
interval = st.selectbox("Choose Timeframe", ["1min", "5min"])

if st.button("📊 Analyze"):
    with st.spinner("Fetching real-time data and analyzing..."):
        df = fetch_candle_data(symbol=symbol, interval=interval, limit=50, api_key=API_KEY)
        if df is not None:
            # ✅ Convert UTC datetime index to IST
            if df.index.tzinfo is None:
                df.index = df.index.tz_localize("UTC")
            df.index = df.index.tz_convert(IST)

            st.success("✅ Data fetched successfully! (Time: IST)")
            st.write(df.tail())

            signal, confidence = analyze_signal(df)
            st.markdown(f"### 📍 **Prediction: {signal.upper()}**")
            st.markdown(f"#### 🔐 Confidence: **{confidence:.2f}%**")
        else:
            st.error("❌ Failed to fetch data.")
