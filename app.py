import streamlit as st import pandas as pd import requests import datetime import pytz import time

---------------------- SETTINGS ----------------------

API_KEY = "899db61d39f640c5bbffc54fab5785e7" ASSETS = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "BTC/USD"] TIMEFRAMES = ["1min", "5min"] TZ = pytz.timezone("Asia/Kolkata")  # IST

---------------------- FUNCTIONS ----------------------

def fetch_candle_data(symbol, interval): url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=50&apikey={API_KEY}" try: response = requests.get(url) data = response.json() if "values" in data: df = pd.DataFrame(data["values"]) df = df.rename(columns={"datetime": "timestamp"}) df["timestamp"] = pd.to_datetime(df["timestamp"]) df = df.sort_values("timestamp") df = df.reset_index(drop=True) df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float) return df else: return None except Exception as e: return None

def calculate_indicators(df): df["EMA"] = df["close"].ewm(span=10, adjust=False).mean() df["RSI"] = compute_rsi(df["close"], 14) df["MACD"] = df["close"].ewm(span=12, adjust=False).mean() - df["close"].ewm(span=26, adjust=False).mean() df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean() df["BB_MA"] = df["close"].rolling(window=20).mean() df["BB_UP"] = df["BB_MA"] + 2 * df["close"].rolling(window=20).std() df["BB_LOW"] = df["BB_MA"] - 2 * df["close"].rolling(window=20).std() return df

def compute_rsi(series, period): delta = series.diff() gain = delta.where(delta > 0, 0) loss = -delta.where(delta < 0, 0) avg_gain = gain.rolling(window=period).mean() avg_loss = loss.rolling(window=period).mean() rs = avg_gain / avg_loss rsi = 100 - (100 / (1 + rs)) return rsi

def generate_signal(df): if df is None or df.shape[0] < 30: return "No data", 0

latest = df.iloc[-1]
previous = df.iloc[-2]

conditions = [
    latest["close"] < latest["BB_LOW"],  # BB bounce
    latest["RSI"] < 30,  # RSI oversold
    latest["MACD"] > latest["Signal"],  # MACD bullish
    latest["close"] > latest["EMA"],  # Above EMA
    latest["close"] > previous["open"] and latest["open"] < previous["close"]  # Green candle engulf
]

score = sum(conditions)

if score >= 4:
    return "UP", score
elif all([
    latest["close"] > latest["BB_UP"],
    latest["RSI"] > 70,
    latest["MACD"] < latest["Signal"],
    latest["close"] < latest["EMA"],
    latest["close"] < previous["open"] and latest["open"] > previous["close"]
]):
    return "DOWN", 5
else:
    return "No Signal", score

---------------------- UI ----------------------

st.set_page_config(page_title="AI Forex Signal Bot", layout="centered") st.title("📈 AI Forex Analyzer (24/7)")

selected_symbol = st.selectbox("Select Asset", ASSETS) selected_tf = st.selectbox("Select Timeframe", TIMEFRAMES)

if st.button("Get Signal"): with st.spinner("Analyzing..."): df = fetch_candle_data(selected_symbol, selected_tf) if df is None: st.error("❌ Failed to fetch data from TwelveData API.") else: df = calculate_indicators(df) signal, confidence = generate_signal(df) timestamp = datetime.datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S") st.subheader(f"🕐 {timestamp} IST") st.markdown(f"Signal: {signal}") st.markdown(f"Confidence: {confidence}/5") st.line_chart(df.set_index("timestamp")["close"])

