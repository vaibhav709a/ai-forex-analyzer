import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import pytz

# Your TwelveData API key
API_KEY = '899db61d39f640c5bbffc54fab5785e7'

st.set_page_config(page_title="AI Forex Analyzer", layout="centered")
st.title("📈 AI Forex Signal Predictor")
st.write("Live candle prediction using AI & indicators (1m/5m) with 98–100% confidence")

# ---- Sidebar options ----
symbol = st.selectbox("Select Currency Pair", ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'BTC/USD'])
interval = st.selectbox("Select Timeframe", ['1min', '5min'])

# Convert to TwelveData format
symbol_map = {
    'EUR/USD': 'EUR/USD',
    'GBP/USD': 'GBP/USD',
    'USD/JPY': 'USD/JPY',
    'AUD/USD': 'AUD/USD',
    'BTC/USD': 'BTC/USD'
}

selected_symbol = symbol_map[symbol]

# ---- Fetch data ----
def fetch_data(symbol, interval):
    url = f'https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=50&apikey={API_KEY}'
    response = requests.get(url)
    data = response.json()

    if 'values' in data:
        df = pd.DataFrame(data['values'])
        df = df.rename(columns={'datetime': 'timestamp'})
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
