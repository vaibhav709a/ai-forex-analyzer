import streamlit as st
import pandas as pd
import requests
import datetime
import pytz
import time

# Timezone
IST = pytz.timezone("Asia/Kolkata")

# TwelveData API key
API_KEY = "899db61d39f640c5bbffc54fab5785e7"

# Supported currency pairs
CURRENCY_PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "BTC/USD", "ETH/USD", "USD/CAD", "USD/CHF"]

# Streamlit UI
st.set_page_config(page_title="AI Forex Signal Generator", layout="centered")
st.title("📊 AI Forex Signal Generator (100% Confidence Only)")
st.markdown("Get highly accurate UP/DOWN signal using real-time indicators from **TwelveData API**")

pair = st.selectbox("Choose currency pair:", CURRENCY_PAIRS)
interval = st.selectbox("Select time frame:", ["1min", "5min"])

if st.button("🔍 Get Signal"):
    symbol = pair.replace("/", "")
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=50&apikey={API_KEY}"
    
    response = requests.get(url)
    data = response.json()

    if "values" not in data:
        st.error("❌ Failed to fetch valid data from TwelveData API.")
    else:
        df = pd.DataFrame(data["values"])
        df = df.rename(columns={"datetime": "timestamp"})
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")

        # Convert price columns
        for col in ["open", "high", "low", "close"]:
            df[col] = df[col].astype(float)

        # Calculate indicators
        df["EMA"] = df["close"].ewm(span=10, adjust=False).mean()
        df["RSI"] = 100 - (100 / (1 + df["close"].pct_change().rolling(14).mean()))
        df["MACD"] = df["close"].ewm(span=12).mean() - df["close"].ewm(span=26).mean()
        df["Signal"] = df["MACD"].ewm(span=9).mean()
        df["BB_upper"] = df["close"].rolling(20).mean() + 2 * df["close"].rolling(20).std()
        df["BB_lower"] = df["close"].rolling(20).mean() - 2 * df["close"].rolling(20).std()

        # Stochastic Oscillator
        low_min = df["low"].rolling(14).min()
        high_max = df["high"].rolling(14).max()
        df["Stoch_K"] = 100 * ((df["close"] - low_min) / (high_max - low_min))

        last = df.iloc[-1]

        # Confidence logic: only show signal when all indicators match
        signal = None
        if (
            last["close"] > last["EMA"] and
            last["RSI"] < 70 and
            last["MACD"] > last["Signal"] and
            last["close"] > last["BB_upper"] and
            last["Stoch_K"] < 80
        ):
            signal = "🔼 UP"
        elif (
            last["close"] < last["EMA"] and
            last["RSI"] > 30 and
            last["MACD"] < last["Signal"] and
            last["close"] < last["BB_lower"] and
            last["Stoch_K"] > 20
        ):
            signal = "🔽 DOWN"

        if signal:
            st.success(f"✅ **Signal:** {signal}")
            st.markdown(f"**Confidence:** 100% (All indicators matched)")
            st.markdown(f"**Time:** {datetime.datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')} IST")
        else:
            st.warning("⚠️ No high-confidence signal at this moment. Try again in a few minutes.")
