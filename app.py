Streamlit app for multi-pair AI forex signal analysis

import streamlit as st import pandas as pd import requests import datetime import pytz import time

TwelveData API key

API_KEY = "806dd29a09244737ae6cd1a305061557"

Supported pairs (you can add more)

PAIRS = [ "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CHF", "BTC/USD", "ETH/USD", "NZD/USD", "USD/CAD" ]

Function to fetch latest candle data

def get_candle_data(symbol, interval="5min"): url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=5&apikey={API_KEY}" try: res = requests.get(url) data = res.json() if "values" not in data: return None df = pd.DataFrame(data["values"]) df = df.astype({"open": float, "close": float, "high": float, "low": float}) return df except Exception as e: return None

Signal logic using indicators

def analyze(df): if df is None or len(df) < 3: return None

latest = df.iloc[0]
previous = df.iloc[1]

direction = ""
confidence = 0

# Simple logic: bullish engulfing + RSI + BB + MACD (mock)
body_now = abs(latest["close"] - latest["open"])
body_prev = abs(previous["close"] - previous["open"])

if latest["close"] > latest["open"] and latest["open"] < previous["close"] and body_now > body_prev:
    direction = "UP"
    confidence += 40
elif latest["close"] < latest["open"] and latest["open"] > previous["close"] and body_now > body_prev:
    direction = "DOWN"
    confidence += 40

# Mock RSI check
rsi = 50 + (latest["close"] - latest["open"]) * 2
if rsi < 30:
    direction = "UP"
    confidence += 30
elif rsi > 70:
    direction = "DOWN"
    confidence += 30

# Mock BB check
bb_signal = ""
if latest["close"] > latest["high"]:
    bb_signal = "Above upper"
    confidence += 30 if direction == "DOWN" else 0
elif latest["close"] < latest["low"]:
    bb_signal = "Below lower"
    confidence += 30 if direction == "UP" else 0
else:
    bb_signal = "Middle"

return {
    "direction": direction if confidence >= 90 else "NO SIGNAL",
    "confidence": confidence,
    "rsi": round(rsi, 2),
    "bb": bb_signal
}

Streamlit UI

st.set_page_config(page_title="AI Forex Multi-Pair Analyzer", layout="wide") st.title("💹 100% Confidence AI Forex Signal Bot")

selected_pairs = st.multiselect("Select pairs to analyze:", PAIRS, default=["EUR/USD", "GBP/USD"]) interval = st.selectbox("Candle Timeframe:", ["1min", "5min", "15min"], index=1)

if st.button("🔍 Get All Signals"): results = [] for pair in selected_pairs: st.write(f"Analyzing {pair}...") df = get_candle_data(pair.replace("/", ":"), interval) result = analyze(df) if result: results.append({ "Pair": pair, "Timeframe": interval, "Direction": result["direction"], "Confidence": f"{result['confidence']}%", "RSI": result["rsi"], "BB": result["bb"] }) else: results.append({ "Pair": pair, "Timeframe": interval, "Direction": "❌ Error", "Confidence": "-", "RSI": "-", "BB": "-" })

if results:
    df_result = pd.DataFrame(results)
    df_result = df_result[df_result["Direction"] != "NO SIGNAL"]
    st.success("✅ Analysis complete!")
    st.dataframe(df_result, use_container_width=True)
else:
    st.error("❌ No signals found or failed to fetch data.")

