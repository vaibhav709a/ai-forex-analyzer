import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Title
st.set_page_config(page_title="Live Forex AI Signal", layout="wide")
st.title("📊 Real-Time Forex Signal Predictor (AI-based)")

# Sidebar inputs
api_key = st.sidebar.text_input("Enter your TwelveData API Key", type="password")
symbol = st.sidebar.selectbox("Select Forex Pair", [
    "EUR/USD", "USD/JPY", "GBP/USD", "USD/CHF", "AUD/USD", "NZD/USD", "USD/CAD", "EUR/JPY", "GBP/JPY", "EUR/GBP"
])
interval = st.sidebar.selectbox("Select Timeframe", ["1min", "5min"])

if not api_key:
    st.warning("Please enter your TwelveData API key to begin.")
    st.stop()

# Format symbol
symbol = symbol.replace("/", "")

# Fetch live data
@st.cache_data(ttl=60)
def get_realtime_data(symbol, interval, api_key):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=100&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    if "values" not in data:
        raise Exception(data.get("message", "Invalid response"))
    df = pd.DataFrame(data["values"])
    df.rename(columns={"datetime": "time"}, inplace=True)
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time")
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col])
    return df

try:
    df = get_realtime_data(symbol, interval, api_key)
    st.line_chart(df.set_index("time")[["open", "high", "low", "close"]])

    # AI logic (simple)
    last_candle = df.iloc[-1]
    second_last = df.iloc[-2]
    signal = "🔼 UP" if last_candle["close"] > last_candle["open"] else "🔽 DOWN"
    confidence = round(abs(last_candle["close"] - last_candle["open"]) / (last_candle["high"] - last_candle["low"] + 1e-6) * 100, 2)

    st.subheader("📌 Prediction")
    st.metric("Signal", signal)
    st.metric("Confidence", f"{confidence}%")
    st.caption(f"Time: {last_candle['time']}")

except Exception as e:
    st.error(f"Error fetching data: {e}")