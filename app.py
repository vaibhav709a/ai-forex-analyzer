import requests
import pandas as pd
import os

TWELVE_DATA_API_KEY = os.getenv("899db61d39f640c5bbffc54fab5785e7")  # Or set directly: "your_api_key"

def fetch_candle_data(symbol="EUR/USD", interval="1min", limit=50):
    symbol = symbol.replace("/", "")
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&apikey={TWELVE_DATA_API_KEY}&outputsize={limit}&format=JSON"
    try:
        response = requests.get(url)
        data = response.json()
        if "values" in data:
            df = pd.DataFrame(data["values"])
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.sort_values("datetime")
            return df
        else:
            return None
    except Exception as e:
        return None
