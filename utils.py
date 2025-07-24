import requests
import datetime

API_KEY = "806dd29a09244737ae6cd1a305061557"

PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD",
    "USD/CHF", "NZD/USD", "EUR/JPY", "EUR/GBP", "GBP/JPY"
]

INTERVALS = ["1min", "5min"]

def fetch_candle_data(symbol, interval):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&apikey={API_KEY}&outputsize=30"
    try:
        res = requests.get(url)
        data = res.json()
        if "values" in data:
            return data["values"]
    except Exception as e:
        print("Fetch error:", e)
    return None

def calculate_confidence(candles):
    try:
        last = candles[0]
        prev = candles[1]
        body_size = abs(float(last["close"]) - float(last["open"]))
        candle_color = "green" if float(last["close"]) > float(last["open"]) else "red"
        big_move = body_size > (abs(float(prev["high"]) - float(prev["low"])) * 0.5)

        if big_move:
            confidence = 100
        else:
            confidence = 70
        return candle_color, confidence
    except Exception as e:
        return None, 0

def analyze_pair(symbol, interval):
    candles = fetch_candle_data(symbol, interval)
    if not candles or len(candles) < 2:
        return None

    color, confidence = calculate_confidence(candles)
    if confidence == 100:
        direction = "📈 UP" if color == "green" else "📉 DOWN"
        return {
            "pair": symbol,
            "interval": interval,
            "signal": direction,
            "confidence": confidence
        }
    return None

def analyze_all_pairs():
    signals = []
    for pair in PAIRS:
        for interval in INTERVALS:
            result = analyze_pair(pair, interval)
            if result:
                signals.append(result)
    return signals
