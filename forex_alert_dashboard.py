import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# ========== Filters ==========

def check_filter(curr_open, curr_high, curr_low, curr_close,
                 prev_open, prev_high, prev_low, prev_close):
    # Filter 1
    if (curr_open < prev_high and
        curr_close < prev_close and
        curr_high > prev_high):
        return "Filter 1"

    # Filter 2
    if (curr_close > prev_low and
        curr_low < prev_low and
        curr_high < prev_high):
        return "Filter 2"
   
    return None


# ========== Assets ==========
forex_pairs = [
    "EURUSD=X","GBPUSD=X","USDJPY=X","USDCHF=X","AUDUSD=X","NZDUSD=X",
    "USDCAD=X","EURGBP=X","EURJPY=X","EURCHF=X","EURAUD=X","EURNZD=X","EURCAD=X",
    "GBPJPY=X","GBPCHF=X","GBPAUD=X","GBPNZD=X","GBPCAD=X",
    "AUDJPY=X","AUDNZD=X","AUDCAD=X","AUDCHF=X",
    "NZDJPY=X","NZDCAD=X","NZDCHF=X",
    "CADJPY=X","CADCHF=X",
    "CHFJPY=X"
]


commodities = [
    "GC=F",   # Gold
    "SI=F",   # Silver
    "CL=F",   # Crude Oil WTI
    "BZ=F",   # Brent Oil
    "NG=F",   # Natural Gas
    "HG=F",   # Copper
    "PL=F",   # Platinum
    "PA=F"    # Palladium
]



indices = [
    "^GSPC",   # S&P 500
    "^DJI",    # Dow Jones
    "^IXIC",   # Nasdaq
    "^FTSE",   # FTSE 100
    "^GDAXI",  # DAX
    "^FCHI",   # CAC 40
    "^N225",   # Nikkei 225
    "^HSI",    # Hang Seng
    "^STOXX50E", # Euro Stoxx 50
    "^AXJO"    # ASX 200
]


assets = forex_pairs + commodities + indices

# Timeframes
timeframes = {
    "Daily": "1d",
    "Weekly": "1wk",
    "Monthly": "1mo"
}


# ========== Streamlit UI ==========
st.set_page_config(page_title="Market Filters Dashboard", layout="wide")
st.title("📊 Market Filters Dashboard")

selected_tf = st.selectbox("Select Timeframe", list(timeframes.keys()))
period_years = st.slider("Backtest Period (years)", 1, 10, 5)


# ========== Backtest Logic ==========
all_results = []

for ticker in assets:
    try:
        df = yf.download(ticker, period=f"{period_years}y", interval=timeframes[selected_tf], progress=False)
        if len(df) < 2:
            continue

        for i in range(1, len(df)):    
            prev = df.iloc[i-1]
            curr = df.iloc[i]
            filter_passed = check_filter(curr["Open"], curr["High"], curr["Low"], curr["Close"],
                                         prev["Open"], prev["High"], prev["Low"], prev["Close"])
            if filter_passed:
                all_results.append([ticker, df.index[i], filter_passed])
    except Exception as e:
        st.write(f"⚠️ Error with {ticker}: {e}")

# Convert to DataFrame
if all_results:
    signals_df = pd.DataFrame(all_results, columns=["Symbol","Date","Filter"])

    # Show recent signals
    st.subheader("📌 Latest Signals")
    latest_signals = signals_df.sort_values("Date", ascending=False).head(50)
    st.dataframe(latest_signals, use_container_width=True)

    # Aggregate counts for chart
    summary = signals_df.groupby(["Date","Filter"]).size().unstack(fill_value=0)

    # Plot stacked bar chart
    st.subheader("📈 Historical Backtest Results")
    fig = px.bar(summary, x=summary.index, y=summary.columns,
                 title=f"Signals by Date ({selected_tf})", barmode="stack")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No signals found for the selected timeframe/period.")


