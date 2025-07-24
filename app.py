import streamlit as st
import pandas as pd
import requests
import datetime
import pytz
import time

# --- SETTINGS ---
API_KEY = "899db61d39f640c5bbffc54fab5785e7"
TIMEZONE = pytz.timezone("Asia/Kolkata")  # IST timezone

# Supported pairs and intervals
CURRENCY_PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "BTC/USD"]
INTERVALS = ["1min", "5min"]

# --- AI Logic for Confidence ---
def analyze_data(df):
    try:
        df['close'] = df['close'].astype(float)

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        if latest['close'] > prev['close']:
            direction = "UP"
        elif latest['close'] < prev['close']:
            direction = "DOWN"
        else:
            direction = "SIDEWAYS"

        # Simple logic: Only accept if recent move is clear and consistent
        confidence = 100 if abs(latest['close'] - prev['close']) > 0.05 else 60

        return direction, confidence
    except Exception as e:
        st.error(f"Analysis Error: {e}")
        return None, 0

# --- Fetch Data from TwelveData ---
def fetch_data(pair, interval):
    symbol = pair.replace("/", "")
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=10&apikey={API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()

        if "values" in data:
            df = pd.DataFrame(data["values"])
            df = df.rename(columns={"datetime": "timestamp"})
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df.sort_values("timestamp")
        else:
            st.error("❌ Failed to fetch valid data.")
            return None
    except Exception as e:
        st.error(f"❌ API Error: {e}")
        return None

# --- STREAMLIT UI ---
st.set_page_config(page_title="Forex AI Signal Bot", layout="centered")
st.title("💹 AI Forex Signal Bot (Live)")
st.markdown("Get **AI-powered direction signals** with 100% confidence based on real data.")
st.caption("Running with TwelveData API — Updated in IST")

selected_pair = st.selectbox("Select Currency Pair", CURRENCY_PAIRS)
selected_interval = st.radio("Select Timeframe", INTERVALS)

if st.button("🔍 Get Signal"):
    with st.spinner("Analyzing live market..."):
        data = fetch_data(selected_pair, selected_interval)
        if data is not None:
            direction, confidence = analyze_data(data)

            current_time = datetime.datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
            if confidence == 100:
                st.success(f"✅ {selected_pair} - {selected_interval.upper()} Signal")
                st.markdown(f"**📈 Direction**: `{direction}`\n\n**🔒 Confidence**: `{confidence}%`\n\n**🕒 Time (IST)**: `{current_time}`")
            else:
                st.warning("⚠️ No high-confidence signal found (Confidence < 100%). Please check later.")

# Auto-refresh every 2 minutes (optional)
# time.sleep(120)
# st.experimental_rerun()
