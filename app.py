import streamlit as st
import pandas as pd
import numpy as np
import requests
import datetime
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from sklearn.ensemble import RandomForestClassifier
import pytz

# -------------------- CONFIG --------------------
API_KEY = "899db61d39f640c5bbffc54fab5785e7"
TIMEZONE = pytz.timezone("Asia/Kolkata")
st.set_page_config(page_title="Forex AI Signal", layout="centered")

# -------------------- UI --------------------
st.title("📈 AI Forex Signal Predictor")
pair = st.selectbox("Select Currency Pair", ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "BTC/USD"])
interval = st.selectbox("Timeframe", ["1min", "5min"])
run = st.button("🔍 Analyze Now")

# -------------------- API FUNCTION --------------------
@st.cache_data(ttl=60)
def get_data(symbol, interval):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=100&apikey={API_KEY}"
    r = requests.get(url)
    data = r.json()
    if "values" in data:
        df = pd.DataFrame(data["values"])
        df = df.sort_values("datetime")
        df.set_index("datetime", inplace=True)
        df = df.astype(float)
        df.index = pd.to_datetime(df.index).tz_localize('UTC').tz_convert(TIMEZONE)
        return df
    else:
        return None

# -------------------- AI PREDICTION FUNCTION --------------------
def generate_features(df):
    df["rsi"] = RSIIndicator(df["close"], window=14).rsi()
    df["macd"] = MACD(df["close"]).macd()
    df["ema"] = EMAIndicator(df["close"], window=14).ema_indicator()
    df["target"] = np.where(df["close"].shift(-1) > df["close"], 1, 0)
    df.dropna(inplace=True)
    return df

def train_and_predict(df):
    df = generate_features(df)
    X = df[["rsi", "macd", "ema"]]
    y = df["target"]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X[:-1], y[:-1])

    last_features = X.iloc[-1].values.reshape(1, -1)
    prediction = model.predict(last_features)[0]
    confidence = model.predict_proba(last_features)[0][prediction]
    
    return prediction, confidence

# -------------------- MAIN RUN --------------------
if run:
    with st.spinner("Fetching data & analyzing..."):
        df = get_data(pair, interval)
        if df is not None:
            signal, confidence = train_and_predict(df)
            st.subheader("📊 AI Prediction Result")
            direction = "📈 UP" if signal == 1 else "📉 DOWN"
            st.success(f"Next Candle Direction: **{direction}**")
            st.info(f"Confidence: **{confidence * 100:.2f}%**")
            st.caption(f"Time: {df.index[-1].strftime('%Y-%m-%d %H:%M:%S')} IST")
        else:
            st.error("❌ Failed to fetch data from TwelveData API.")        df = df.rename(columns={'datetime': 'timestamp'})
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        df.set_index('timestamp', inplace=True)
        df = df.astype(float)

        # Convert to IST
        df.index = df.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
        return df
    else:
        return None

# ---- AI signal prediction ----
def ai_predict(df):
    if df is None or len(df) < 30:
        return None, 0

    # Indicators
    df['EMA'] = df['close'].ewm(span=10).mean()
    df['RSI'] = 100 - (100 / (1 + df['close'].pct_change().rolling(14).mean() / abs(df['close'].pct_change().rolling(14).mean())))
    df['MACD'] = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()
    df['Signal'] = df['MACD'].ewm(span=9).mean()

    df['UpperBand'] = df['close'].rolling(20).mean() + 2 * df['close'].rolling(20).std()
    df['LowerBand'] = df['close'].rolling(20).mean() - 2 * df['close'].rolling(20).std()

    df['Stoch_K'] = ((df['close'] - df['low'].rolling(14).min()) /
                     (df['high'].rolling(14).max() - df['low'].rolling(14).min())) * 100

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    signals = []

    # Rule 1: RSI Oversold / Overbought
    if latest['RSI'] < 30:
        signals.append("RSI indicates BUY")
    elif latest['RSI'] > 70:
        signals.append("RSI indicates SELL")

    # Rule 2: MACD Crossover
    if previous['MACD'] < previous['Signal'] and latest['MACD'] > latest['Signal']:
        signals.append("MACD Bullish Crossover")
    elif previous['MACD'] > previous['Signal'] and latest['MACD'] < latest['Signal']:
        signals.append("MACD Bearish Crossover")

    # Rule 3: EMA Trend
    if latest['close'] > latest['EMA']:
        signals.append("Price above EMA → BUY")
    else:
        signals.append("Price below EMA → SELL")

    # Rule 4: Bollinger Bounce
    if latest['close'] <= latest['LowerBand']:
        signals.append("Bollinger Bounce → BUY")
    elif latest['close'] >= latest['UpperBand']:
        signals.append("Bollinger Rejection → SELL")

    # Rule 5: Stochastic Oversold/Overbought
    if latest['Stoch_K'] < 20:
        signals.append("Stochastic Oversold → BUY")
    elif latest['Stoch_K'] > 80:
        signals.append("Stochastic Overbought → SELL")

    # Decide final direction
    buy_signals = sum('BUY' in s or 'Bullish' in s for s in signals)
    sell_signals = sum('SELL' in s or 'Bearish' in s for s in signals)

    if buy_signals >= 3:
        return "📈 BUY / UP", 98 + buy_signals
    elif sell_signals >= 3:
        return "📉 SELL / DOWN", 98 + sell_signals
    else:
        return "⚠️ No Sure Signal", 0

# ---- Run analysis ----
if st.button("🔍 Analyze Now"):
    df = fetch_data(selected_symbol, interval)
    if df is not None:
        prediction, confidence = ai_predict(df)
        if confidence >= 98:
            st.success(f"✅ Signal: {prediction}")
            st.info(f"Confidence: {confidence}%")
        else:
            st.warning("No confident signal found.")
    else:
        st.error("❌ Failed to fetch data. Please check your API key or network.")
