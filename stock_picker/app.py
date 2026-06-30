"""Streamlit app for daily stock picks using the 150-day moving average."""

import streamlit as st
import yfinance as yf

from stock_picker.config import DEFAULT_TICKERS, ScreenerSettings
from stock_picker.screener import picks_to_dataframe, screen_stocks

st.set_page_config(
    page_title="Daily Stock Picker",
    page_icon="📈",
    layout="wide",
)

st.title("Daily Stock Picker")
st.caption("Screens stocks daily using the **150-day moving average**")

with st.sidebar:
    st.header("Screening rules")
    top_n = st.slider("Number of picks", min_value=3, max_value=25, value=10)
    require_above_ma = st.checkbox("Price must be above 150 MA", value=True)
    require_rising_ma = st.checkbox("150 MA must be rising", value=True)
    max_pct_above = st.slider("Max % above 150 MA", min_value=5, max_value=30, value=15)
    min_volume = st.number_input(
        "Min avg daily volume",
        min_value=100_000,
        max_value=10_000_000,
        value=500_000,
        step=100_000,
    )

    st.divider()
    st.markdown(
        """
        **How it works**
        1. Fetches recent price history for each stock
        2. Calculates the 150-day moving average
        3. Keeps stocks trading **above** a rising 150 MA
        4. Ranks by strength without being overextended
        """
    )

settings = ScreenerSettings(
    top_n=top_n,
    require_price_above_ma=require_above_ma,
    require_rising_ma=require_rising_ma,
    max_pct_above_ma=float(max_pct_above),
    min_avg_volume=int(min_volume),
)

if st.button("Run today's screen", type="primary", use_container_width=True):
    with st.spinner("Screening stocks against the 150-day moving average..."):
        picks = screen_stocks(settings)
        st.session_state["picks"] = picks
        st.session_state["settings"] = settings

if "picks" in st.session_state:
    picks = st.session_state["picks"]
    settings = st.session_state["settings"]

    if not picks:
        st.warning("No stocks matched your criteria today. Try relaxing the filters.")
    else:
        df = picks_to_dataframe(picks)
        df_display = df.rename(
            columns={
                "ticker": "Ticker",
                "price": "Price ($)",
                "ma_150": "150 MA ($)",
                "pct_above_ma": "% Above MA",
                "ma_slope_pct": "MA Slope (%)",
                "avg_volume": "Avg Volume",
                "signal": "Signal",
                "score": "Score",
            }
        )

        st.subheader(f"Today's top {len(picks)} picks")
        st.dataframe(
            df_display.style.format(
                {
                    "Price ($)": "${:.2f}",
                    "150 MA ($)": "${:.2f}",
                    "% Above MA": "{:.2f}%",
                    "MA Slope (%)": "{:.2f}%",
                    "Avg Volume": "{:,.0f}",
                    "Score": "{:.2f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Price vs 150-day moving average")
        selected = st.selectbox("Inspect a pick", [p.ticker for p in picks])

        if selected:
            history = yf.Ticker(selected).history(period="1y", auto_adjust=True)
            if not history.empty:
                history["MA150"] = history["Close"].rolling(window=150).mean()
                chart_df = history[["Close", "MA150"]].dropna()
                st.line_chart(chart_df, use_container_width=True)

                pick = next(p for p in picks if p.ticker == selected)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Price", f"${pick.price:.2f}")
                c2.metric("150 MA", f"${pick.ma_150:.2f}")
                c3.metric("% Above MA", f"{pick.pct_above_ma:.2f}%")
                c4.metric("MA slope (20d)", f"{pick.ma_slope_pct:.2f}%")
else:
    st.info("Click **Run today's screen** to generate daily investment picks.")
    st.markdown(f"Universe: **{len(DEFAULT_TICKERS)}** large-cap stocks")
