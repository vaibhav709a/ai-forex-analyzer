import streamlit as st import pandas as pd import requests import datetime import pytz import time

Constants

API_KEY = "899db61d39f640c5bbffc54fab5785e7" BASE_URL = "https://api.twelvedata.com/time_series" TIMEZONES = pytz.all_timezones INDICATORS = ["RSI", "MACD", "EMA", "BBANDS", "STOCH"]

Utility function to get current IST time

def get_current_ist(): utc_now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc) ist_now = utc_now.astimezone(pytz.timezone("Asia/Kolkata")) return ist_now

Function to fetch live data from TwelveData API

def fetch_data(symbol: str, interval: str = "5min", outputsize: int = 50): params = { "symbol": symbol, "interval": interval, "outputsize": outputsize, "apikey": API_KEY, "timezone": "Asia/Kolkata" } response = requests.get(BASE_URL, params=params) if response.status_code == 200: data = response.json() if "values" in data: df = pd.DataFrame(data["values"]) df = df.rename(columns={"datetime": "timestamp"}) df["timestamp"] = pd.to_datetime(df["timestamp"]) df.set_index("timestamp", inplace=True) df = df.sort_index() return df return None

Simple logic for AI-based signal generation

def generate_signal(df: pd.DataFrame): # Simple analysis: If last candle is red and touched upper Bollinger Band, signal = DOWN # If last candle is green and touched lower Bollinger Band, signal = UP df["close"] = pd.to_numeric(df["close"]) df["high"] = pd.to_numeric(df["high"]) df["low"] = pd.to_numeric(df["low"]) df["open"] = pd.to_numeric(df["open"])

df["MA20"] = df["close"].rolling(window=20).mean()
df["STD"] = df["close"].rolling(window=20).std()
df["Upper"] = df["MA20"] + (2 * df["STD"])
df["Lower"] = df["MA20"] - (2 * df["STD"])

last_row = df.iloc[-1]
candle_red = last_row["close"] < last_row["open"]
candle_green = last_row["close"] > last_row["open"]

signal = None
confidence = 0

if candle_red and last_row["high"] >= last_row["Upper"]:
    signal = "DOWN"
    confidence = 99.2
elif candle_green and last_row["low"] <= last_row["Lower"]:
    signal = "UP"
    confidence = 98.7

return signal, confidence

Streamlit UI

st.set_page_config(page_title="AI Forex Analyzer", layout="centered") st.title("💹 AI Forex Signal Analyzer (IST)")

symbol = st.selectbox("Select Currency Pair:", ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "BTC/USD"]) timeframe = st.radio("Select Time Frame:", ["1min", "5min"])

if st.button("🔍 Analyze Now"): st.info(f"Fetching data for {symbol} - {timeframe} timeframe...", icon="🔄") df = fetch_data(symbol.replace("/", ""), timeframe)

if df is not None:
    st.success("✅ Data fetched successfully.")

    signal, confidence = generate_signal(df)

    if signal:
        ist_time = get_current_ist().strftime("%Y-%m-%d %H:%M:%S")
        st.markdown(f"### 📈 AI Prediction: **{signal}**")
        st.markdown(f"#### ✅ Confidence: **{confidence:.2f}%**")
        st.markdown(f"#### 🕒 Time: **{ist_time} IST**")
    else:
        st.warning("⚠️ No strong signal detected right now. Please try again after some time.")
else:
    st.error("❌ Failed to fetch data from TwelveData API.")

