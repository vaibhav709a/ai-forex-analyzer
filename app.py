import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz

# === CONFIG ===
API_KEY = "899db61d39f640c5bbffc54fab5785e7"  # Your TwelveData API key
IST = pytz.timezone("Asia/Kolkata")

# === UI ===
st.set_page_config(page_title="AI Forex Analyzer", layout="centered")
st.title("📈 AI Forex Direction Predictor (1m/5m)")
st.markdown("**Live signal with AI confirmation & confidence score (IST)**")

pair = st.selectbox("Select Currency Pair", ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "BTC/USD"])
interval = st.radio("Timeframe", ["1min", "5min"])

# === DATA FETCH ===
def fetch_data(symbol, interval):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=50&apikey={API_KEY}"
    r = requests.get(url)
    data = r.json()

    if "values" in data:
        df = pd.DataFrame(data["values"])
        df = df.rename(columns={'datetime': 'timestamp'})
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df = df.sort_index()

        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC').tz_convert(IST)
        else:
            df.index = df.index.tz_convert(IST)

        df = df.astype(float)
        return df
    else:
        st.error("❌ Failed to fetch data from TwelveData API.")
        return None

# === INDICATOR LOGIC ===
def analyze(df):
    df["EMA10"] = df["close"].ewm(span=10).mean()
    df["EMA20"] = df["close"].ewm(span=20).mean()
    df["MACD"] = df["close"].ewm(span=12).mean() - df["close"].ewm(span=26).mean()
    df["Signal"] = df["MACD"].ewm(span=9).mean()
    df["RSI"] = compute_rsi(df["close"])

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    decision = "⏳ Wait"
    confidence = 0

    if latest["EMA10"] > latest["EMA20"] and latest["MACD"] > latest["Signal"] and latest["RSI"] < 70:
        decision = "⬆️ Buy (UP)"
        confidence += 33
    if latest["EMA10"] < latest["EMA20"] and latest["MACD"] < latest["Signal"] and latest["RSI"] > 30:
        decision = "⬇️ Sell (DOWN)"
        confidence += 33

    # Candle confirmation
    if latest["close"] > latest["open"]:
        confidence += 34 if decision == "⬆️ Buy (UP)" else 0
    elif latest["close"] < latest["open"]:
        confidence += 34 if decision == "⬇️ Sell (DOWN)" else 0

    if confidence >= 98:
        return decision, confidence
    else:
        return "⏳ Wait", confidence

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# === MAIN ===
if pair and interval:
    st.info("🔄 Fetching real-time data...")
    df = fetch_data(pair.replace("/", ""), interval)
    if df is not None:
        decision, confidence = analyze(df)
        st.subheader("🔍 AI Forecast:")
        st.success(f"Next Candle Direction: **{decision}**")
        st.metric("Confidence", f"{confidence} %")
        st.line_chart(df["close"], use_container_width=True)
