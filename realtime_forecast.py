import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import pytz
import os

# Load API key securely
API_KEY = st.secrets.get("899db61d39f640c5bbffc54fab5785e7", "")

def fetch_candle_data(symbol, interval='5min', limit=50):
    if not API_KEY:
        st.error("❌ API key is missing. Please set it in Streamlit secrets.")
        return None

    endpoint = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": limit,
        "apikey": API_KEY,
        "format": "JSON"
    }

    response = requests.get(endpoint, params=params)
    
    try:
        data = response.json()
        if "status" in data and data["status"] == "error":
            st.error(f"❌ API Error: {data.get('message', 'Unknown error')}")
            return None
        
        if "values" not in data:
            st.error("❌ Unexpected response structure from API.")
            return None

        df = pd.DataFrame(data["values"])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values("datetime")
        return df

    except Exception as e:
        st.error(f"❌ Failed to fetch data: {e}")
        return None
