import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Forex Signal Analyzer", layout="centered")

st.title("📈 AI Forex Analyzer")

API_KEY = "899db61d39f640c5bbffc54fab5785e7"  # Replace with your real TwelveData API key
SYMBOL = "EUR/USD"
INTERVAL = "5min"
TIMEZONE = "Asia/Kolkata"

def fetch_data():
    url = f"https://api.twelvedata.com/time_series?symbol={SYMBOL}&interval={INTERVAL}&outputsize=30&apikey={API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        st.error("❌ Failed to connect to TwelveData API.")
        return None

    data = response.json()

    if "values" not in data:
        st.error("❌ No data returned from TwelveData.")
        return None

    try:
        df = pd.DataFrame(data["values"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)
        df = df.sort_index()

        # Ensure timezone-aware datetime in IST
        df.index = df.index.tz_localize("UTC").tz_convert(TIMEZONE)
        return df

    except Exception as e:
        st.error(f"❌ Data formatting error: {e}")
        return None

df = fetch_data()

if df is not None:
    st.success("✅ Data fetched successfully!")

    st.subheader("📊 Latest Data (IST)")
    st.dataframe(df.tail(10))

    latest_candle = df.iloc[-1]
    prev_candle = df.iloc[-2]

    st.subheader("🧠 Signal Analysis")

    if float(latest_candle["close"]) > float(prev_candle["close"]):
        st.success("📈 Signal: UP (Buy)")
    elif float(latest_candle["close"]) < float(prev_candle["close"]):
        st.error("📉 Signal: DOWN (Sell)")
    else:
        st.info("⏸ Signal: No movement")
else:
    st.stop()
