import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Universal Market Scanner", layout="wide")

# -------------------------
# Filter logic
# -------------------------

def check_filter(curr_open, curr_high, curr_low, curr_close,
                 prev_open, prev_high, prev_low, prev_close):
    """Return 'Filter 1' or 'Filter 2' or None"""
    # Filter 1
    if (curr_open < prev_high and curr_close < prev_close and curr_high > prev_high):
        return "Filter 1"
    # Filter 2
    if (curr_close > prev_low and curr_low < prev_low and curr_high < prev_high):
        return "Filter 2"
    return None    

# -------------------------
# Asset lists
# -------------------------
forex_pairs = [
    "EURUSD=X","GBPUSD=X","USDJPY=X","USDCHF=X","AUDUSD=X","NZDUSD=X",
    "USDCAD=X","EURGBP=X","EURJPY=X","EURCHF=X","EURAUD=X","EURNZD=X","EURCAD=X",
    "GBPJPY=X","GBPCHF=X","GBPAUD=X","GBPNZD=X","GBPCAD=X",
    "AUDJPY=X","AUDNZD=X","AUDCAD=X","AUDCHF=X",
    "NZDJPY=X","NZDCAD=X","NZDCHF=X",
    "CADJPY=X","CADCHF=X","CHFJPY=X"
]


commodities = [
    "GC=F", "SI=F", "CL=F", "BZ=F", "NG=F", "HG=F", "PL=F", "PA=F"
]

indices = [
    "^GSPC", "^DJI", "^IXIC", "^FTSE", "^GDAXI", "^FCHI",
    "^N225", "^HSI", "^STOXX50E", "^AXJO"
]

ASSET_GROUPS = {
    "Forex": forex_pairs,
    "Commodities": commodities,
    "Indices": indices,
    "All": forex_pairs + commodities + indices
}

# -------------------------
# Timeframe mapping
# -------------------------
TF_TO_INTERVAL = {
    "1H": "1h",
    "4H": "1h",   # resample from 1h
    "1D": "1d",
    "1W": "1wk",
    "1M": "1mo"
}


DEFAULT_PERIOD = {
    "1H": "90d",
    "4H": "90d",
    "1D": "3y",
    "1W": "8y",
    "1M": "12y"
}

# -------------------------
# Yahoo → TradingView mapping
# -------------------------
YF_TO_TV = {
    # Forex
    "EURUSD=X": "FX:EURUSD", "GBPUSD=X": "FX:GBPUSD", "USDJPY=X": "FX:USDJPY", "USDCHF=X": "FX:USDCHF",
    "AUDUSD=X": "FX:AUDUSD", "NZDUSD=X": "FX:NZDUSD", "USDCAD=X": "FX:USDCAD", "EURGBP=X": "FX:EURGBP",
    "EURJPY=X": "FX:EURJPY", "EURCHF=X": "FX:EURCHF", "EURAUD=X": "FX:EURAUD", "EURNZD=X": "FX:EURNZD",
    "EURCAD=X": "FX:EURCAD", "GBPJPY=X": "FX:GBPJPY", "GBPCHF=X": "FX:GBPCHF", "GBPAUD=X": "FX:GBPAUD",
    "GBPNZD=X": "FX:GBPNZD", "GBPCAD=X": "FX:GBPCAD", "AUDJPY=X": "FX:AUDJPY", "AUDNZD=X": "FX:AUDNZD",
    "AUDCAD=X": "FX:AUDCAD", "AUDCHF=X": "FX:AUDCHF", "NZDJPY=X": "FX:NZDJPY", "NZDCAD=X": "FX:NZDCAD",
    "NZDCHF=X": "FX:NZDCHF", "CADJPY=X": "FX:CADJPY", "CADCHF=X": "FX:CADCHF", "CHFJPY=X": "FX:CHFJPY",

    # Commodities
    "GC=F": "COMEX:GC1!", "SI=F": "COMEX:SI1!", "CL=F": "NYMEX:CL1!", "BZ=F": "ICEEU:BRN1!",
    "NG=F": "NYMEX:NG1!", "HG=F": "COMEX:HG1!", "PL=F": "NYMEX:PL1!", "PA=F": "NYMEX:PA1!",

    # Indices
    "^GSPC": "SP:SPX", "^DJI": "DJ:DJI", "^IXIC": "NASDAQ:IXIC", "^FTSE": "TVC:UKX",
    "^GDAXI": "XETR:DAX", "^FCHI": "EURONEXT:PX1", "^N225": "TVC:NI225", "^HSI": "TVC:HSI",
    "^STOXX50E": "STOXX:SX5E", "^AXJO": "ASX:XJO"
}


# TradingView interval mapping
TF_TO_TV_INTERVAL = {
    "1H": "60",
    "4H": "240",
    "1D": "D",
    "1W": "W",
    "1M": "M"
}

# -------------------------
# Data fetch
# -------------------------
@st.cache_data(show_spinner=False)
def fetch_ohlc(ticker: str, interval: str, period: str):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, threads=False)
        if df is None or df.empty:
            return None
        df = df.dropna(how="all")
        return df
    except Exception:
        return None




# -------------------------
# Sidebar
# -------------------------
st.sidebar.header("Scanner Options")
asset_group = st.sidebar.selectbox("Asset group", list(ASSET_GROUPS.keys()), index=3)
timeframe = st.sidebar.selectbox("Timeframe", ["1H","4H","1D","1W","1M"], index=2)
filter_choice = st.sidebar.selectbox("Filter to apply", ["Filter 1","Filter 2","Both"], index=2)
run_backtest = st.sidebar.checkbox("Run historical backtest", value=False)
backtest_years = st.sidebar.slider("Backtest window (years)", 1, 12, 5)

if st.sidebar.button("Run Scan"):
    st.session_state.scan_now = True
else:
    if "scan_now" not in st.session_state:
        st.session_state.scan_now = False

# -------------------------
# Main
# -------------------------
st.title("Universal Market Scanner — Chartink-style")


if not st.session_state.scan_now:
    st.info("Click **Run Scan** to begin.")
    st.stop()

results = []
backtest_records = []

yf_period = f"{backtest_years}y" if run_backtest and timeframe in ["1D","1W","1M"] else DEFAULT_PERIOD.get(timeframe, "1y")
if timeframe in ["1H","4H"] and run_backtest:
    yf_period = "90d"


assets = ASSET_GROUPS[asset_group]
progress = st.progress(0)


for i, ticker in enumerate(assets, start=1):
    progress.progress(round(i/len(assets),2))

    interval = TF_TO_INTERVAL[timeframe]
    df = fetch_ohlc(ticker, interval, yf_period)
    if df is None or len(df) < 2:
        continue

    if timeframe == "4H":
        df = df.resample("4H").agg({"Open":"first","High":"max","Low":"min","Close":"last"}).dropna()

    df = df.sort_index()

    # Backtest
    if run_backtest:
        for idx in range(1, len(df)):
            prev, curr = df.iloc[idx-1], df.iloc[idx]
            f = check_filter(curr["Open"], curr["High"], curr["Low"], curr["Close"],
                             prev["Open"], prev["High"], prev["Low"], prev["Close"])
            if f:
                backtest_records.append({"Symbol": ticker, "Date": df.index[idx], "Filter": f})

     # Latest bar
     prev, curr = df.iloc[-2], df.iloc[-1]
     f = check_filter(curr["Open"], curr["High"], curr["Low"], curr["Close"],
                     prev["Open"], prev["High"], prev["Low"], prev["Close"])
     if f and (filter_choice == "Both" or filter_choice == f):
         results.append({
             "Symbol": ticker, "Filter": f, "Time": df.index[-1],
            "Open": float(curr["Open"]), "High": float(curr["High"]),
            "Low": float(curr["Low"]), "Close": float(curr["Close"])
        })



progress.empty()

# -------------------------
# Show results
# -------------------------
st.subheader(f"Scanner Results — {len(results)} matches")
if results:
    df_res = pd.DataFrame(results)
    st.dataframe(df_res.sort_values(["Filter","Symbol"]), use_container_width=True)

    symbol = st.selectbox("Select symbol", df_res["Symbol"].unique())
    if symbol:
        chart_period = "90d" if timeframe in ["1H","4H"] else "1y"
        df_chart = fetch_ohlc(symbol, TF_TO_INTERVAL[timeframe], chart_period)
        if df_chart is not None:
            if timeframe == "4H":
                df_chart = df_chart.resample("4H").agg({"Open":"first","High":"max","Low":"min","Close":"last"}).dropna()
            df_chart = df_chart.tail(200)

            # Plotly candlestick
            fig = go.Figure(data=[go.Candlestick(
                x=df_chart.index, open=df_chart["Open"], high=df_chart["High"],
                low=df_chart["Low"], close=df_chart["Close"]
            )])
            fig.update_layout(title=f"{symbol} - {timeframe}", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # TradingView embed
            st.markdown("### Live TradingView Chart")
            tv_symbol = YF_TO_TV.get(symbol)
            tv_interval = TF_TO_TV_INTERVAL[timeframe]
            if tv_symbol:
                tv_html = f"""
                <iframe src="https://s.tradingview.com/widgetembed/?symbol={tv_symbol}&interval={tv_interval}&hidesidetoolbar=1&symboledit=1&saveimage=1&toolbarbg=f1f3f6&theme=light&style=1&timezone=Etc/UTC"
                width="100%" height="600" frameborder="0" allowtransparency="true" scrolling="no"></iframe>
                """
                st.components.v1.html(tv_html, height=600)
            else:
                st.warning(f"No TradingView mapping for {symbol}.")

else:
    st.info("No symbols matched the filters.")

# -------------------------
# Backtest chart
# -------------------------
if run_backtest:
    st.subheader("Historical Backtest")
    if backtest_records:
        df_bt = pd.DataFrame(backtest_records)
        summary = df_bt.groupby(["Date","Filter"]).size().unstack(fill_value=0).sort_index()
        fig2 = px.bar(summary, x=summary.index, y=summary.columns, barmode="stack", title="Signals over time")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No backtest signals found.")



