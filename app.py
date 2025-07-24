import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import pytz

# Your new API key
API_KEY = "806dd29a09244737ae6cd1a305061557"

# List of supported pairs
PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "BTC/USD"
]

# Map to TwelveData format
PAIR_MAP = {
    "EUR/USD": "EUR/USD",
    "GBP/USD": "GBP/USD",
    "USD/JPY": "USD/JPY",
    "AUD/USD": "AUD/USD",
    "BTC/USD": "BTC/USD"
}

# Function to fetch data
def fetch_data(symbol, interval):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=50&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    if "values" not in data:
        return None

    df = pd.DataFrame(data["values"])
    df = df.rename(columns={"datetime": "timestamp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col])

    return df

# Signal logic: all indicators must align
def analyze(df):
    close = df["close"]

    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    macd_signal = macd_line.ewm(span=9, adjust=False).mean()

    # EMA
    ema_fast = close.ewm(span=5).mean()
    ema_slow = close.ewm(span=20).mean()

    # Bollinger Bands
    sma = close.rolling(20).mean()
    std = close.rolling(20).std()
    upper_bb = sma + 2 * std
    lower_bb = sma - 2 * std

    # Get last value
    if len(close) < 21:
        return "NO SIGNAL", 0

    last_rsi = rsi.iloc[-1]
    last_macd = macd_line.iloc[-1]
    last_signal = macd_signal.iloc[-1]
    last_ema_fast = ema_fast.iloc[-1]
    last_ema_slow = ema_slow.iloc[-1]
    last_price = close.iloc[-1]
    last_upper = upper_bb.iloc[-1]
    last_lower = lower_bb.iloc[-1]

    # Determine signal
    indicators = []

    if last_macd > last_signal:
        indicators.append("UP")
    elif last_macd < last_signal:
        indicators.append("DOWN")

    if last_ema_fast > last_ema_slow:
        indicators.append("UP")
    elif last_ema_fast < last_ema_slow:
        indicators.append("DOWN")

    if last_price < last_lower:
        indicators.append("UP")
    elif last_price > last_upper:
        indicators.append("DOWN")

    if last_rsi < 30:
        indicators.append("UP")
    elif last_rsi > 70:
        indicators.append("DOWN")

    # Final Signal
    if indicators.count("UP") == 4:
        return "UP", 100
    elif indicators.count("DOWN") == 4:
        return "DOWN", 100
    else:
        return "NO SIGNAL", 0

# App UI
st.set_page_config(page_title="AI Forex Signal", layout="centered")
st.title("💹 AI Forex Signal (100% Confidence Only)")
st.markdown("Get **1-minute or 5-minute signals** powered by AI logic using real indicators.")

pair = st.selectbox("Select Currency Pair", PAIRS)
interval = st.selectbox("Timeframe", ["1min", "5min"])
btn = st.button("🔍 Get Signal")

if btn:
    with st.spinner("Analyzing market..."):
        symbol = PAIR_MAP[pair]
        df = fetch_data(symbol, interval)

        if df is None or df.empty:
            st.error("❌ Failed to fetch valid data from TwelveData API.")
        else:
            signal, confidence = analyze(df)

            now_ist = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
            st.write(f"🕒 Time (IST): `{now_ist}`")

            if confidence == 100:
                st.success(f"✅ Signal: **{signal}** with 100% confidence")
            else:
                st.warning("⚠️ No sureshot signal at the moment. Please check again later.")
