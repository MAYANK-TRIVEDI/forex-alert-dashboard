import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime

forex_pairs = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCHF=X", "NZDUSD=X",
    "USDCAD=X", "EURGBP=X", "EURJPY=X", "GBPJPY=X"
]

timeframes = {
    "1H": "60m",
    "4H": "60m",  # Will resample to 4H
    "D": "1d",
    "W": "1wk",
    "M": "1mo"
}


def resample_4h(df):
    # Make sure index is datetime and sorted
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

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
    # All should be scalar floats
    try:
        c_close = float(current['Close'])
        c_low = float(current['Low'])
        c_high = float(current['High'])
        p_low = float(previous['Low'])
        p_high = float(previous['High'])
    except Exception as e:
        st.error(f"Data conversion error: {e}")
        return False

    return (c_close > p_low) and (c_low < p_low) and (c_high < p_high)



def fetch_and_check(pair, tf_label, tf_interval):
    # Set period to fetch data sufficiently long for each timeframe
    if tf_interval == '60m':
        period = "10d"
    elif tf_interval == '1d':
        period = "60d"
    elif tf_interval == '1wk':
        period = "365d"
    else:
        period = "730d"

    df = yf.download(tickers=pair, interval=tf_interval, period=period, progress=False)

    # Validate data exists and has required columns
    if df.empty or len(df) < 2:
        return False

    if tf_label == "4H":
        # Resample 60m data to 4H
        df = resample_4h(df)
        if len(df) < 2:
            return False

    # Get the last two complete candles
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

st_autorefresh = st.checkbox("Auto refresh every 10 minutes", value=False)
if st_autorefresh:
    st.experimental_rerun()


