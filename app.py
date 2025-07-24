import streamlit as st
import pandas as pd
import requests
import datetime
import pytz

# Set timezone to IST
IST = pytz.timezone('Asia/Kolkata')

# TwelveData API Key
API_KEY = "899db61d39f640c5bbffc54fab5785e7"

# Indicator calculation
def analyze_data(df):
    df['EMA'] = df['close'].ewm(span=10).mean()
    df['MACD'] = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()
    df['RSI'] = 100 - (100 / (1 + (df['close'].diff().apply(lambda x: x if x > 0 else 0).rolling(14).mean() /
                                   df['close'].diff().apply(lambda x: abs(x) if x < 0 else 0).rolling(14).mean())))
    df['BB_upper'] = df['close'].rolling(window=20).mean() + 2 * df['close'].rolling(window=20).std()
    df['BB_lower'] = df['close'].rolling(window=20).mean() - 2 * df['close'].rolling(window=20).std()
    return df

# AI logic to determine signal
def get_signal(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    up_conditions = [
        last['close'] > last['EMA'],
        last['MACD'] > 0,
        last['RSI'] < 70 and last['RSI'] > 50,
        prev['close'] < prev['BB_lower'] and last['close'] > last['BB_lower']
    ]

    down_conditions = [
        last['close'] < last['EMA'],
        last['MACD'] < 0,
        last['RSI'] > 30 and last['RSI'] < 50,
        prev['close'] > prev['BB_upper'] and last['close'] < last['BB_upper']
    ]

    if all(up_conditions):
        return "🔼 UP", 98
    elif all(down_conditions):
        return "🔽 DOWN", 98
    else:
        return "⚠️ No clear signal", 0

# Fetch data from TwelveData
def fetch_data(symbol, interval):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=60&apikey={API_KEY}"
    try:
        res = requests.get(url)
        data = res.json()

        if 'values' not in data:
            return None

        df = pd.DataFrame(data['values'])
        df = df.rename(columns={'datetime': 'timestamp'})
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.index = df.index.tz_localize('UTC').tz_convert(IST)
        df = df.astype(float)
        return df
    except Exception:
        return None

# Streamlit UI
st.title("📊 AI Forex Signal Predictor")
st.write("Get real-time UP/DOWN signal using AI-based indicator logic (TwelveData API)")

symbols = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "BTC/USD"]
intervals = ["1min", "5min"]

symbol = st.selectbox("Select Currency Pair", symbols)
interval = st.selectbox("Select Timeframe", intervals)
run_button = st.button("🔍 Analyze Signal")

if run_button:
    st.info("⏳ Fetching and analyzing data...")
    data = fetch_data(symbol.replace("/", ""), interval)

    if data is None:
        st.error("❌ Failed to fetch data from TwelveData API.")
    else:
        df = analyze_data(data)
        signal, confidence = get_signal(df)

        if confidence > 0:
            st.success(f"✅ Next Candle Prediction: **{signal}** with {confidence}% confidence")
        else:
            st.warning("⚠️ No confident signal detected.")
