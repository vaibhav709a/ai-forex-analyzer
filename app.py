import streamlit as st
import pandas as pd
import requests
import datetime
import pytz

# Your TwelveData API Key
API_KEY = "899db61d39f640c5bbffc54fab5785e7"

# List of supported Forex pairs
PAIR_LIST = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "BTC/USD"]

# Timeframe options
TIMEFRAMES = ["1min", "5min"]

# Convert to IST
def get_ist_time():
    utc_time = datetime.datetime.utcnow()
    ist = pytz.timezone("Asia/Kolkata")
    return utc_time.replace(tzinfo=pytz.utc).astimezone(ist)

# Fetch historical data
def fetch_data(symbol, interval):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=50&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if "values" in data:
        df = pd.DataFrame(data["values"])
        df = df.rename(columns={"datetime": "timestamp"})
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")
        df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)
        return df
    return None

# Calculate indicators
def add_indicators(df):
    df["ema"] = df["close"].ewm(span=14).mean()
    df["rsi"] = 100 - (100 / (1 + df["close"].pct_change().rolling(14).mean()))
    df["macd"] = df["close"].ewm(span=12).mean() - df["close"].ewm(span=26).mean()
    df["signal"] = df["macd"].ewm(span=9).mean()
    df["bb_upper"] = df["close"].rolling(20).mean() + 2 * df["close"].rolling(20).std()
    df["bb_lower"] = df["close"].rolling(20).mean() - 2 * df["close"].rolling(20).std()
    return df

# Generate signal
def get_signal(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    confidence = 0
    direction = None

    # Check EMA
    if last["close"] > last["ema"]:
        confidence += 1
    elif last["close"] < last["ema"]:
        confidence -= 1

    # Check RSI
    if last["rsi"] < 30:
        confidence += 1
    elif last["rsi"] > 70:
        confidence -= 1

    # MACD Crossover
    if last["macd"] > last["signal"] and prev["macd"] < prev["signal"]:
        confidence += 1
    elif last["macd"] < last["signal"] and prev["macd"] > prev["signal"]:
        confidence -= 1

    # Bollinger Bounce
    if last["close"] < last["bb_lower"]:
        confidence += 1
    elif last["close"] > last["bb_upper"]:
        confidence -= 1

    # Final decision
    if confidence >= 4:
        return "UP", 100
    elif confidence <= -4:
        return "DOWN", 100
    else:
        return "NO SIGNAL", int((abs(confidence) / 4) * 100)

# Streamlit UI
st.set_page_config(page_title="Forex AI Analyzer", layout="centered")
st.title("📈 AI Forex Signal Generator (24/7)")
st.markdown("Live signals based on EMA, RSI, MACD, Bollinger Bands\n**Only 100% confidence trades shown**")

symbol = st.selectbox("Select Currency Pair", PAIR_LIST)
interval = st.selectbox("Select Timeframe", TIMEFRAMES)

if st.button("📊 Get Signal"):
    df = fetch_data(symbol.replace("/", ""), interval)
    if df is not None:
        df = add_indicators(df)
        signal, conf = get_signal(df)
        current_time = get_ist_time().strftime("%Y-%m-%d %H:%M:%S")

        if signal == "NO SIGNAL":
            st.warning(f"⚠️ No 100% confidence signal detected at {current_time} IST.")
        else:
            st.success(f"✅ Signal: **{signal}** | Confidence: **{conf}%** at {current_time} IST")
    else:
        st.error("❌ Failed to fetch valid data from TwelveData API.")
