import streamlit as st
from utils import analyze_all_pairs, PAIRS

st.set_page_config(page_title="Forex AI Signal Bot", layout="wide")

st.title("📈 AI-Powered Forex Signal Bot (1m & 5m)")

interval = st.selectbox("Select Candle Timeframe:", ["1min", "5min"])

if st.button("🔍 Check All Pairs Now"):
    with st.spinner("Analyzing market..."):
        signals = analyze_all_pairs(interval)
        if signals:
            for signal in signals:
                st.success(signal)
        else:
            st.warning("⚠️ No 100% sureshot signals found right now.")
