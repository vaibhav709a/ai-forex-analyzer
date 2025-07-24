import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz

# Set IST timezone
IST = pytz.timezone("Asia/Kolkata")

# Replace with your TwelveData API Key
API_KEY = "899db61d39f640c5bbffc54fab5785e7"

# Supported assets
ASSETS = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "BTC/USD"]

# Timeframe options
TIMEFRAMES = {
    "1 Minute": "1min",
    "5 Minute": "5min"
}

# --- Functions ---

def fetch_data(symbol, interval):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=50&apikey={API_KEY}&format=JSON"
    try:
        response = requests.get(url)
        data = response.json()
        if "values" in data:
            df = pd.DataFrame(data["values"])
            df = df.rename(columns={"datetime": "timestamp"})
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.set_index("timestamp")
            df = df.sort_index()
            df.index = df.index.tz_localize("UTC").tz_convert("Asia/Kolkata")
            df = df.astype(float, errors="ignore")
            return df
        else:
            st.error("❌ Failed to fetch data from TwelveData API.")
            return None
    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        return None

def calculate_indicators(df):
    df["EMA20"] = df["close"].ewm(span=20).mean()
    df["RSI"] = compute_rsi(df["close"], 14)
    df["MACD"] = df["close"].ewm(span=12).mean() - df["close"].ewm(span=26).mean()
    df["Signal"] = df["MACD"].ewm(span=9).mean()
    return df

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def predict_signal(df):
    latest = df.iloc[-1]
    previous = df.iloc[-2]

    conditions = []

    if latest["close"] > latest["EMA20"]:
        conditions.append("price_above_ema")

    if latest["RSI"] < 30:
        conditions.append("rsi_oversold")
    elif latest["RSI"] > 70:
        conditions.append("rsi_overbought")

    if latest["MACD"] > latest["Signal"]:
        conditions.append("macd_bullish")
    else:
        conditions.append("macd_bearish")

    # AI-like logic for signal prediction
    if all(cond in conditions for cond in ["price_above_ema", "rsi_oversold", "macd_bullish"]):
        return "📈 UP", 98
    elif all(cond in conditions for cond in ["price_above_ema", "rsi_overbought", "macd_bearish"]):
        return "📉 DOWN", 98
    else:
        return "⏸ No Clear Signal", 70

# --- Streamlit UI ---

st.set_page_config(page_title="AI Forex Analyzer", layout="centered")
st.title("💹 AI Forex Signal Predictor")

symbol = st.selectbox("Select Currency Pair", ASSETS)
timeframe_label = st.selectbox("Select Timeframe", list(TIMEFRAMES.keys()))
timeframe = TIMEFRAMES[timeframe_label]

if st.button("🔍 Analyze"):
    with st.spinner("Fetching and analyzing data..."):
        df = fetch_data(symbol.replace("/", ""), timeframe)
        if df is not None:
            df = calculate_indicators(df)
            signal, confidence = predict_signal(df)

            st.subheader("📊 Signal Prediction")
            st.success(f"Next Candle: **{signal}** (Confidence: {confidence}%)")

            st.line_chart(df[["close", "EMA20"]].tail(30))

            st.dataframe(df.tail(5)[["close", "EMA20", "RSI", "MACD", "Signal"]])
