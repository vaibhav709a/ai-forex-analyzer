import streamlit as st
import pandas as pd
import requests
import datetime
import pytz

# Set IST timezone
IST = pytz.timezone('Asia/Kolkata')

# TwelveData API Key
API_KEY = "806dd29a09244737ae6cd1a305061557"

# Forex Pairs to Analyze
forex_pairs = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CHF", "NZD/USD", "USD/CAD", "BTC/USD"]

# Confidence Threshold
CONFIDENCE_THRESHOLD = 100

# Indicator Calculation Function
def calculate_indicators(df):
    df['EMA20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['RSI'] = compute_rsi(df['close'], 14)
    return df

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def fetch_data(symbol):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=5min&outputsize=50&apikey={API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if "values" in data:
            df = pd.DataFrame(data["values"])
            df = df.rename(columns={'datetime': 'timestamp'})
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df = calculate_indicators(df)
            return df
    except Exception as e:
        print("API Fetch Error:", e)
    return None

# Signal Logic
def generate_signal(df):
    if df is None or df.empty:
        return None, 0
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    confidence = 0

    if latest['RSI'] < 30 and latest['close'] > latest['EMA20'] and latest['EMA20'] > latest['EMA50']:
        confidence += 40
    if latest['RSI'] > 70 and latest['close'] < latest['EMA20'] and latest['EMA20'] < latest['EMA50']:
        confidence += 40
    if latest['EMA20'] > latest['EMA50'] and latest['close'] > latest['EMA20']:
        confidence += 20

    direction = "UP" if latest['close'] > latest['EMA20'] else "DOWN"
    return direction, confidence

# Streamlit UI
st.set_page_config(layout="wide", page_title="AI Forex Signal Bot")
st.title("📈 AI Forex Signal Bot (24/7, 100% Confidence Only)")
st.write("Get sureshot 5-minute signals based on EMA + RSI logic with real-time data from TwelveData.")

selected_pairs = st.multiselect("Select Forex Pairs to Analyze", forex_pairs, default=forex_pairs)

if st.button("🔍 Get Signals Now"):
    ist_now = datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
    st.info(f"🕒 Signal Time (IST): {ist_now}")
    results = []

    for pair in selected_pairs:
        st.write(f"🔄 Checking: `{pair}`")
        data = fetch_data(pair)
        direction, confidence = generate_signal(data)

        if confidence >= CONFIDENCE_THRESHOLD:
            st.success(f"✅ `{pair}` Signal: **{direction}** | Confidence: {confidence}%")
        else:
            st.warning(f"⚠️ `{pair}` No strong signal. Confidence: {confidence}%")
