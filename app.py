import streamlit as st
from utils import analyze_all_pairs, PAIRS

st.set_page_config(page_title="AI Forex Analyzer", layout="wide")
st.title("📊 AI Forex Signal Analyzer")
st.markdown("✅ Only shows signals with 100% confidence (Strong Logic)")

if st.button("🔍 Analyze All Pairs Now"):
    results = analyze_all_pairs()
    if results:
        for res in results:
            st.success(f"{res['pair']} ({res['interval']}): {res['signal']} — Confidence: {res['confidence']}%")
    else:
        st.warning("No strong signals (100% confidence) found at this moment.")
