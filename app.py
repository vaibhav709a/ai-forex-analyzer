
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import ta

st.set_page_config(page_title="AI Forex Signal", layout="wide")

# Constants
API_KEY = "137b57f565344e8a8e568ccfc6db4696"
BASE_URL = "https://api.twelvedata.com/time_series"

# Currency options and timeframes
forex_pairs = [
    "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD",
    "USD/CHF", "NZD/USD", "EUR/GBP", "EUR/JPY", "GBP/JPY"
]
timeframes = {"1 Minute": "1min", "5 Minutes": "5min"}

# Functions
def fetch_data(symbol, interval):
    params = {
        "symbol": symbol,
        "interval": interval,
        "apikey": API_KEY,
        "outputsize": 50,
        "format": "JSON"
    }
    r = requests.get(BASE_URL, params=params)
    try:
        data = r.json().get("values", [])
        df = pd.DataFrame(data)
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.sort_values("datetime")
        df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def analyze(df):
    df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()
    macd = ta.trend.MACD(df["close"])
    df["macd"] = macd.macd_diff()
    df["ema20"] = ta.trend.EMAIndicator(df["close"], window=20).ema_indicator()
    df["ema50"] = ta.trend.EMAIndicator(df["close"], window=50).ema_indicator()
    bb = ta.volatility.BollingerBands(df["close"])
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    return df

def generate_signal(df):
    last = df.iloc[-1]
    score = 0
    if last["rsi"] < 30: score += 1  # oversold
    if last["macd"] > 0: score += 1
    if last["ema20"] > last["ema50"]: score += 1
    if last["close"] < last["bb_lower"]: score += 1

    if score >= 3:
        direction = "🔼 UP (Buy)"
    elif last["rsi"] > 70 and last["macd"] < 0 and last["ema20"] < last["ema50"] and last["close"] > last["bb_upper"]:
        direction = "🔽 DOWN (Sell)"
    else:
        direction = "🚫 No Strong Signal"

    confidence = int((score / 4) * 100)
    return direction, confidence

# UI
st.title("💹 AI Forex Signal Analyzer")
pair = st.selectbox("Select Currency Pair", forex_pairs)
tf_name = st.radio("Select Timeframe", list(timeframes.keys()))
tf = timeframes[tf_name]

# Main
df = fetch_data(pair.replace("/", ""), tf)
if not df.empty:
    df = analyze(df)
    signal, confidence = generate_signal(df)
    st.subheader(f"📊 Next Candle Signal: {signal}")
    st.write(f"Confidence: **{confidence}%**")
    st.line_chart(df.set_index("datetime")[["close", "bb_upper", "bb_lower"]])
else:
    st.warning("No data to analyze yet.")
