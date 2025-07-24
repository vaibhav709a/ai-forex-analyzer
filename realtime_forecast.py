import requests
import pandas as pd
import numpy as np

def fetch_candle_data(symbol, interval="1min", limit=50, api_key="demo"):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize={limit}&apikey={api_key}"
    response = requests.get(url)
    try:
        data = response.json()
        if "values" in data:
            df = pd.DataFrame(data["values"])
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.astype({
                "open": float, "high": float,
                "low": float, "close": float
            }).sort_values("datetime")
            return df
        else:
            return None
    except Exception as e:
        print("Error fetching candle data:", e)
        return None

def analyze_signal(df):
    # Add real indicator logic (simplified for demo)
    df["ema"] = df["close"].ewm(span=10).mean()
    df["rsi"] = compute_rsi(df["close"], 14)

    last_close = df["close"].iloc[-1]
    last_ema = df["ema"].iloc[-1]
    last_rsi = df["rsi"].iloc[-1]

    if last_close > last_ema and last_rsi < 70:
        return "UP", 98.5
    elif last_close < last_ema and last_rsi > 30:
        return "DOWN", 97.8
    else:
        return "NO TRADE", 90.0

def compute_rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up = up.rolling(period).mean()
    ma_down = down.rolling(period).mean()
    rs = ma_up / ma_down
    rsi = 100 - (100 / (1 + rs))
    return rsi
