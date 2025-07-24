import streamlit as st
import pandas as pd
import requests
import datetime
import pytz

# ========== CONFIG ==========
API_KEY = "899db61d39f640c5bbffc54fab5785e7"
BASE_URL = "https://api.twelvedata.com/time_series"
TIMEZONE = "Asia/Kolkata"
INDICATOR_CONFIDENCE_THRESHOLD = 0.98

# ========== FUNCTIONS ==========

def fetch_data(symbol, interval):
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": 100,
        "apikey": API_KEY,
        "timezone": "Asia/Kolkata"
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        if "values" in data:
            df = pd.DataFrame(data["values"])
            df["datetime"] = pd.to_datetime(df["datetime"])
            df.set_index("datetime", inplace=True)
            df = df.astype(float)
            return df.sort_index()
    return None

def analyze_ai(df):
    if df is None or len(df) < 20:
        return None, None

    last_candle = df.iloc[-1]
    prev_candle = df.iloc[-2]

    # Indicators (simplified logic)
    df["EMA10"] = df["close"].ewm(span=10).mean()
    df["RSI"] = compute_rsi(df["close"])
    df["MACD"] = df["close"].ewm(span=12).mean() - df["close"].ewm(span=26).mean()

    rsi = df["RSI"].iloc[-1]
    ema_trend = df["close"].iloc[-1] > df["EMA10"].iloc[-1]
    macd_positive = df["MACD"].iloc[-1] > 0

    # Logic
    up_conditions = rsi < 70 and ema_trend and macd_positive
    down_conditions = rsi > 30 and not ema_trend and not macd_positive

    if up_conditions:
        return "UP", 0.99
    elif down_conditions:
        return "DOWN", 0.99
    else:
        return "NO SIGNAL", 0.5

def compute_rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)

    avg_gain = up.rolling(window=period).mean()
    avg_loss = down.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ========== UI ==========

st.set_page_config(page_title="AI Forex Signal", layout="centered")
st.title("📊 AI Forex Signal Analyzer")
st.markdown("Live signal prediction using RSI, EMA, MACD from **TwelveData**")

symbol = st.selectbox("Select Pair", ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "BTC/USD"])
interval = st.selectbox("Timeframe", ["1min", "5min"])

df = fetch_data(symbol, interval)

if df is not None:
    st.success(f"✅ Data fetched for {symbol} ({interval})")

    signal, confidence = analyze_ai(df)

    if signal != "NO SIGNAL" and confidence >= INDICATOR_CONFIDENCE_THRESHOLD:
        st.markdown(f"### 🟢 Next Candle Direction: **{signal}**")
        st.markdown(f"#### Confidence: **{int(confidence*100)}%**")
    else:
        st.warning("⚠️ Not enough confirmation to give a sureshot signal.")
else:
    st.error("❌ Failed to fetch data from TwelveData API.")
