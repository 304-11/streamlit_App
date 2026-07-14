import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Global Top10 Market Cap Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("🌍 Global Top 10 Market Cap Stock Dashboard")
st.markdown("최근 1년간 글로벌 시가총액 Top10 기업의 주가를 비교합니다.")

# ----------------------------------------------------
# Global Market Cap Top10
# ----------------------------------------------------

TOP10 = {
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Apple": "AAPL",
    "Amazon": "AMZN",
    "Alphabet": "GOOGL",
    "Meta": "META",
    "Saudi Aramco": "2222.SR",
    "Broadcom": "AVGO",
    "Tesla": "TSLA",
    "Berkshire Hathaway": "BRK-B"
}

# ----------------------------------------------------
# Sidebar
# ----------------------------------------------------

st.sidebar.header("설정")

selected = st.sidebar.multiselect(
    "기업 선택",
    list(TOP10.keys()),
    default=list(TOP10.keys())
)

normalize = st.sidebar.checkbox(
    "100 기준 정규화",
    value=True
)

# ----------------------------------------------------
# Download
# ----------------------------------------------------

@st.cache_data(ttl=3600)
def load_price(tickers):

    data = yf.download(
        tickers,
        period="1y",
        auto_adjust=True,
        progress=False
    )

    return data["Close"]

if len(selected) == 0:
    st.warning("기업을 선택하세요.")
    st.stop()

symbols = [TOP10[x] for x in selected]

prices = load_price(symbols)

prices.columns = selected

# ----------------------------------------------------
# Normalize
# ----------------------------------------------------

plot_df = prices.copy()

if normalize:
    plot_df = plot_df / plot_df.iloc[0] * 100

plot_df = plot_df.reset_index()

plot_df = plot_df.melt(
    id_vars="Date",
    var_name="Company",
    value_name="Price"
)

# ----------------------------------------------------
# Plotly
# ----------------------------------------------------

title = (
    "최근 1년 주가 변화 (Normalized=100)"
    if normalize
    else "최근 1년 종가"
)

fig = px.line(
    plot_df,
    x="Date",
    y="Price",
    color="Company",
    title=title
)

fig.update_layout(
    height=650,
    hovermode="x unified",
    legend_title="Company",
    xaxis_title="Date",
    yaxis_title="Price",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------
# Metrics
# ----------------------------------------------------

st.subheader("📊 Summary")

rows = []

for company in selected:

    ticker = TOP10[company]

    stock = yf.Ticker(ticker)

    info = stock.fast_info

    current = prices[company].iloc[-1]
    first = prices[company].iloc[0]

    ret = (current - first) / first * 100

    marketcap = info.get("market_cap", None)

    rows.append({
        "Company": company,
        "Ticker": ticker,
        "Current Price": round(current,2),
        "1Y Return (%)": round(ret,2),
        "Market Cap": marketcap
    })

summary = pd.DataFrame(rows)

st.dataframe(
    summary,
    use_container_width=True,
    hide_index=True
)

# ----------------------------------------------------
# Raw Data
# ----------------------------------------------------

with st.expander("원본 데이터 보기"):

    st.dataframe(prices)
