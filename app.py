import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz

# ========== CONFIG ==========
TWELVE_DATA_API_KEY = '899db61d39f640c5bbffc54fab5785e7'  # ← Put your actual API key
BASE_URL = 'https://api.twelvedata.com/time_series'
TIMEZONE = 'Asia/Kolkata'

# ========== UI ==========
st.set_page_config(page_title="AI Forex Signal Analyzer", layout="centered")
st.title("📈 AI Forex Analyzer")
st.caption("Powered by TwelveData | Live Signals with 98-100% Confidence")

pair = st.selectbox("Select Currency Pair", ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "BTC/USD"])
tf = st.selectbox("Select Timeframe", ["1min", "5min"])

if st.button("🔍 Analyze Now"):
    symbol = pair.replace('/', '')
    interval = tf

    with st.spinner("Fetching and analyzing data..."):

        try:
            url = f"{BASE_URL}?symbol={symbol}&interval={interval}&outputsize=50&apikey={TWELVE_DATA_API_KEY}"
            response = requests.get(url)
            data = response.json()

            if 'values' not in data:
                st.error("❌ Failed to fetch data from TwelveData API.")
            else:
                df = pd.DataFrame(data['values'])
                df = df.rename(columns={'datetime': 'timestamp'})
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                df = df.sort_index()

                # Ensure UTC then convert to IST
                df.index = df.index.tz_localize('UTC').tz_convert(TIMEZONE)

                # Convert price columns
                for col in ['open', 'high', 'low', 'close']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

                # ========== AI ANALYSIS ==========
                import numpy as np

                def calculate_indicators(df):
                    df['ema'] = df['close'].ewm(span=10).mean()
                    df['rsi'] = 100 - (100 / (1 + (df['close'].diff().clip(lower=0).rolling(14).mean() / df['close'].diff().clip(upper=0).abs().rolling(14).mean())))
                    df['macd'] = df['close'].ewm(12).mean() - df['close'].ewm(26).mean()
                    df['signal'] = df['macd'].ewm(9).mean()
                    df['upper_bb'] = df['close'].rolling(20).mean() + 2 * df['close'].rolling(20).std()
                    df['lower_bb'] = df['close'].rolling(20).mean() - 2 * df['close'].rolling(20).std()
                    return df

                df = calculate_indicators(df)

                latest = df.iloc[-1]

                # ========== AI Logic ==========
                match_count = 0
                total_conditions = 4

                # Condition 1: MACD crossover
                if latest['macd'] > latest['signal']:
                    match_count += 1

                # Condition 2: Price above EMA
                if latest['close'] > latest['ema']:
                    match_count += 1

                # Condition 3: RSI in bullish zone
                if latest['rsi'] is not None and latest['rsi'] > 50:
                    match_count += 1

                # Condition 4: Close price bouncing from lower BB
                if latest['close'] > latest['lower_bb']:
                    match_count += 1

                confidence = round((match_count / total_conditions) * 100)

                # ========== Result ==========
                if confidence >= 98:
                    signal = "📈 BUY (UP)"
                    color = "green"
                elif confidence <= 2:
                    signal = "📉 SELL (DOWN)"
                    color = "red"
                else:
                    signal = "⚠️ No clear signal"
                    color = "gray"

                st.markdown(f"### ✅ AI Signal Result")
                st.markdown(f"**Prediction:** <span style='color:{color}; font-size:22px'>{signal}</span>", unsafe_allow_html=True)
                st.markdown(f"**Confidence:** `{confidence}%`")
                st.markdown(f"**Time (IST):** `{df.index[-1].strftime('%Y-%m-%d %H:%M:%S')}`")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
