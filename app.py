import streamlit as st
import requests
import pandas as pd
import pytz
from datetime import datetime

# YOUR TwelveData API Key here
API_KEY = "899db61d39f640c5bbffc54fab5785e7"

# Indicator-based AI analysis function
def analyze_signals(df):
    try:
        df['EMA20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['RSI'] = compute_rsi(df['close'], 14)
        df['Upper'], df['Middle'], df['Lower'] = compute_bollinger_bands(df['close'])
        df['MACD'], df['Signal'] = compute_macd(df['close'])

        last = df.iloc[-1]
        signals = []

        if last['close'] > last['Upper']:
            signals.append("Overbought (BB)")
        if last['RSI'] > 70:
            signals.append("RSI Overbought")
        if last['MACD'] > last['Signal']:
            signals.append("MACD Bullish")

        if last['close'] < last['Lower']:
            signals.append("Oversold (BB)")
        if last['RSI'] < 30:
            signals.append("RSI Oversold")
        if last['MACD'] < last['Signal']:
            signals.append("MACD Bearish")

        # Decision logic
        up_conf = sum(sig in signals for sig in ["Oversold (BB)", "RSI Oversold", "MACD Bullish"])
        down_conf = sum(sig in signals for sig in ["Overbought (BB)", "RSI Overbought", "MACD Bearish"])

        if up_conf >= 2:
            return "📈 UP", up_conf * 33
        elif down_conf >= 2:
            return "📉 DOWN", down_conf * 33
        else:
            return "❓ No clear signal", 50

    except Exception as e:
        st.error(f"Signal analysis error: {e}")
        return "Error", 0

# Helper functions
def compute_rsi(series, period):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def compute_bollinger_bands(series, window=20):
    sma = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    upper = sma + 2 * std
    lower = sma - 2 * std
    return upper, sma, lower

def compute_macd(series):
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

# UI
st.set_page_config(page_title="Forex AI Signal", layout="wide")
st.title("💹 AI Forex Signal Analyzer (Live)")

pair = st.selectbox("Select Currency Pair", ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "BTC/USD"])
interval = st.selectbox("Timeframe", ["1min", "5min"])

symbol = pair.replace("/", "")
url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=100&apikey={API_KEY}"

response = requests.get(url)
data = response.json()

if "values" not in data:
    st.error("❌ Failed to fetch data from TwelveData API.")
else:
    df = pd.DataFrame(data['values'])
    df = df.rename(columns={"datetime": "timestamp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)
    df = df.sort_index()

    # Convert to IST
    df.index = df.index.tz_localize("UTC").tz_convert("Asia/Kolkata")

    # Convert values
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    st.line_chart(df["close"].tail(50))

    direction, confidence = analyze_signals(df)
    st.subheader(f"📊 Next Signal: {direction}")
    st.write(f"🔍 Confidence: {confidence}%")
    st.caption(f"Last updated: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')} IST")
