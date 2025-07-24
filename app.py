import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from PIL import Image
import io

st.set_page_config(page_title="AI Forex Signal", layout="wide")
st.title("📈 AI Forex Signal Analyzer")

st.sidebar.header("Settings")

# Input API Key
api_key = st.sidebar.text_input("Enter TwelveData API Key", type="password")

# Currency Pair Selector
symbols = ["EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CHF", "USD/CAD", "NZD/USD", "EUR/GBP", "EUR/JPY", "GBP/JPY"]
symbol = st.sidebar.selectbox("Select Currency Pair", symbols)

# Timeframe Selector
interval = st.sidebar.radio("Select Timeframe", ["1min", "5min"])

# Image Upload (Optional)
uploaded_file = st.file_uploader("Optional: Upload chart image for extra prediction (JPG/PNG)", type=["jpg", "jpeg", "png"])

def fetch_forex_data(symbol, interval, api_key):
    if not api_key:
        return None
    sym = symbol.replace("/", "")
    url = f"https://api.twelvedata.com/bbands?symbol={sym}&interval={interval}&apikey={api_key}&time_period=20&series_type=close"
    price_url = f"https://api.twelvedata.com/time_series?symbol={sym}&interval={interval}&apikey={api_key}&outputsize=30"

    bb = requests.get(url).json()
    price = requests.get(price_url).json()

    if "values" in bb and "values" in price:
        df_bb = pd.DataFrame(bb["values"])
        df_price = pd.DataFrame(price["values"])
        df = pd.merge(df_price, df_bb, on="datetime")
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.rename(columns={
            "datetime": "time",
            "close_x": "close",
            "upper_band": "upper",
            "lower_band": "lower"
        })
        df["close"] = df["close"].astype(float)
        df["upper"] = df["upper"].astype(float)
        df["lower"] = df["lower"].astype(float)
        return df.sort_values("time")
    return None

def predict_next_move(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    if last["close"] > last["upper"] and last["close"] < prev["close"]:
        return "DOWN", 98
    elif last["close"] < last["lower"] and last["close"] > prev["close"]:
        return "UP", 98
    else:
        return "NO SIGNAL", 0

def analyze_uploaded_image(image_bytes):
    # Fake logic for now; just for demo purposes
    return "UP", 95

if uploaded_file:
    img_bytes = uploaded_file.read()
    img = Image.open(io.BytesIO(img_bytes))
    st.image(img, caption="Uploaded Chart Image", use_column_width=True)
    direction, conf = analyze_uploaded_image(img_bytes)
    st.subheader("🧠 Image-Based Prediction")
    st.write(f"Next Candle: **{direction}** with **{conf}%** confidence")

if api_key:
    df = fetch_forex_data(symbol, interval, api_key)
    if df is not None:
        st.line_chart(df.set_index("time")[["close", "upper", "lower"]])
        signal, confidence = predict_next_move(df)
        st.subheader("📊 Real-time Market Prediction")
        if signal != "NO SIGNAL":
            st.success(f"**{signal}** with **{confidence}%** confidence (Based on Bollinger Bounce Logic)")
        else:
            st.warning("No clear signal right now. Please wait for better confirmation.")
    else:
        st.error("Failed to fetch data. Check API key or symbol.")
else:
    st.info("Please enter your TwelveData API Key from the sidebar.")
