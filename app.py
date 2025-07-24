import streamlit as st
import pandas as pd
import requests
import datetime
import pytz
import time

# Your TwelveData API key
API_KEY = "806dd29a09244737ae6cd1a305061557"

# Timezone conversion: UTC to IST
def convert_to_ist(utc_time_str):
    utc_time = datetime.datetime.strptime(utc_time_str, "%Y-%m-%d %H:%M:%S")
    utc_time = utc_time.replace(tzinfo=pytz.utc)
    ist_time = utc_time.astimezone(pytz.timezone("Asia/Kolkata"))
    return ist_time.strftime("%Y-%m-%d %H:%M:%S")

# Available currency pairs
PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "BTC/USD"]

# Streamlit UI
st.title("🧠 AI Forex Signal Analyzer")
pair = st.selectbox("Choose currency pair", PAIRS)
interval = st.selectbox("Select Timeframe", ["1min", "5min"])
if st.button("🔍 Get Signal"):

    symbol = pair.replace("/", "")
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=10&apikey={API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()

        if "values" not in data:
            st.error("❌ Failed to fetch valid data from TwelveData API.")
        else:
            df = pd.DataFrame(data["values"])
            df = df.rename(columns={'datetime': 'timestamp'})
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')

            # Convert UTC to IST
            df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')

            # Calculate simple indicators
            df['close'] = df['close'].astype(float)
            df['ema'] = df['close'].ewm(span=10, adjust=False).mean()
            df['rsi'] = df['close'].diff().apply(lambda x: max(x, 0)).rolling(14).mean() / \
                        df['close'].diff().abs().rolling(14).mean() * 100
            df['macd'] = df['close'].ewm(span=12, adjust=False).mean() - df['close'].ewm(span=26, adjust=False).mean()

            latest = df.iloc[-1]

            # AI-like logic for signal (simplified)
            confidence = 0
            if latest['close'] > latest['ema']:
                confidence += 33
            if latest['rsi'] < 30:
                confidence += 33
            if latest['macd'] > 0:
                confidence += 34

            direction = "UP" if confidence == 100 else "NO TRADE"
            time_ist = latest['timestamp'].strftime("%Y-%m-%d %H:%M:%S")

            if confidence == 100:
                st.success(f"✅ Signal: {direction} at {time_ist} IST\nConfidence: 100%")
            else:
                st.warning(f"⚠️ No strong signal right now. Confidence: {confidence}%")

    except Exception as e:
        st.error("❌ Failed to fetch data from TwelveData API.")
        st.write(str(e))
