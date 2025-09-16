import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime

# Forex pairs in Yahoo Finance format
forex_pairs = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCHF=X", "NZDUSD=X",
    "USDCAD=X", "EURGBP=X", "EURJPY=X", "GBPJPY=X"
]

timeframes = {
    "1H": "60m",
    "4H": "60m",  # Will resample
    "D": "1d",
    "W": "1wk",
    "M": "1mo"
}

def resample_4h(df):
    ohlc_dict = {
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }
    df_4h = df.resample('4H').apply(ohlc_dict).dropna()
    return df_4h


def check_condition(current, previous):
    return (
        current['Close'] > previous['Low'] and
        current['Low'] < previous['Low'] and
        current['High'] < previous['High']
    )


def fetch_and_check(pair, tf_label, tf_interval):
    if tf_interval == '60m':
        period = "10d"
    elif tf_interval == '1d':
        period = "60d"
    elif tf_interval == '1wk':
        period = "365d"
    else:
        period = "730d"
    df = yf.download(tickers=pair, interval=tf_interval, period=period, progress=False)

    if df.empty or len(df) < 2:
        return False

    if tf_label == "4H":
        df = resample_4h(df)
        if len(df) < 2:
            return False

    previous = df.iloc[-2]
    current = df.iloc[-1]

    return check_condition(current, previous)


def run_scan():
    matches = []
    for pair in forex_pairs:
        for tf_label, tf_interval in timeframes.items():
            try:
                if fetch_and_check(pair, tf_label, tf_interval):
                    matches.append((pair, tf_label))
            except Exception as e:
                st.error(f"Error processing {pair} {tf_label}: {e}")
    return matches

# Streamlit UI
st.title("Forex Pairs Alert Dashboard")
st.write("Checking condition: Current candle vs previous candle on same timeframe")


if st.button("Run Scan"):
    with st.spinner("Scanning..."):
        matched_pairs = run_scan()

    if matched_pairs:
        st.success(f"Found {len(matched_pairs)} matching pairs!")
        for pair, tf in matched_pairs:
            st.markdown(f"✅ **{pair}** on **{tf}** timeframe")
    else:
        st.info("No pairs matched the condition at this time.")

st.write("---")
st.caption("Last update: " + datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))

# Optional: Auto-refresh every 10 minutes
st_autorefresh = st.checkbox("Auto refresh every 10 minutes", value=False)
if st_autorefresh:
    st.experimental_rerun()


