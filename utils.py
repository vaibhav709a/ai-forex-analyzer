import requests
import pandas as pd
import ta

API_KEY = '806dd29a09244737ae6cd1a305061557'
BASE_URL = 'https://api.twelvedata.com/time_series'

# Supported pairs (add/remove if needed)
PAIRS = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'BTC/USD']

def fetch_data(symbol, interval):
    params = {
        'symbol': symbol,
        'interval': interval,
        'apikey': API_KEY,
        'outputsize': 100
    }
    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()

        if 'values' not in data:
            print(f"❌ Error fetching {symbol} - {data.get('message', 'Unknown error')}")
            return None

        df = pd.DataFrame(data['values'])
        df = df.rename(columns={
            'datetime': 'time',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close'
        })
        df = df.astype({'open': 'float', 'high': 'float', 'low': 'float', 'close': 'float'})
        df = df.sort_values('time')
        return df
    except Exception as e:
        print(f"❌ Exception fetching data for {symbol}: {e}")
        return None

def calculate_indicators(df):
    # Bollinger Bands
    bb = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()

    # RSI
    df['rsi'] = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi()

    # Stochastic
    stoch = ta.momentum.StochasticOscillator(high=df['high'], low=df['low'], close=df['close'])
    df['stoch_k'] = stoch.stoch()
    df['stoch_d'] = stoch.stoch_signal()

    return df

def check_signal(df):
    if df is None or df.empty:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]
    confidence = 0
    direction = None

    # Condition 1: Bollinger Band bounce
    if last['close'] > last['bb_upper'] and last['close'] < prev['close']:
        confidence += 1
        direction = 'DOWN'
    elif last['close'] < last['bb_lower'] and last['close'] > prev['close']:
        confidence += 1
        direction = 'UP'

    # Condition 2: RSI
    if last['rsi'] < 30:
        confidence += 1
        direction = 'UP'
    elif last['rsi'] > 70:
        confidence += 1
        direction = 'DOWN'

    # Condition 3: Stochastic crossover
    if last['stoch_k'] > last['stoch_d'] and last['stoch_k'] < 20:
        confidence += 1
        direction = 'UP'
    elif last['stoch_k'] < last['stoch_d'] and last['stoch_k'] > 80:
        confidence += 1
        direction = 'DOWN'

    if confidence >= 3:
        return f"✅ {direction} Signal ({confidence}/3 matched)"
    else:
        return None

def analyze_all_pairs(interval='1min'):
    results = []
    for pair in PAIRS:
        print(f"Checking {pair} - {interval}...")
        df = fetch_data(pair, interval)
        if df is not None:
            df = calculate_indicators(df)
            signal = check_signal(df)
            if signal:
                results.append(f"{pair} ({interval}): {signal}")
    return results
