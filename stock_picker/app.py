"""Streamlit app for daily stock picks — optimized for phone browsers."""

import streamlit as st
import yfinance as yf

from stock_picker.config import DEFAULT_TICKERS, ScreenerSettings
from stock_picker.screener import screen_stocks

st.set_page_config(
    page_title="Daily Stock Picker",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .pick-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.75rem;
      }
      .pick-card h3 { margin: 0 0 0.35rem 0; font-size: 1.35rem; }
      .pick-card p  { margin: 0.15rem 0; color: #cbd5e1; font-size: 0.95rem; }
      .hero { text-align: center; margin-bottom: 0.5rem; }
      div[data-testid="stMetric"] {
        background: #1e293b;
        border-radius: 10px;
        padding: 0.5rem;
      }
      .block-container { padding-top: 1.25rem; max-width: 720px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_pick_card(pick, rank: int) -> None:
    st.markdown(
        f"""
        <div class="pick-card">
          <h3>#{rank} {pick.ticker}</h3>
          <p><strong>${pick.price:.2f}</strong> · 150 MA ${pick.ma_150:.2f}</p>
          <p>{pick.pct_above_ma:.2f}% above MA · MA slope {pick.ma_slope_pct:.2f}%</p>
          <p>{pick.signal} · score {pick.score:.2f}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown('<div class="hero"><h1>📈 Daily Stock Picker</h1></div>', unsafe_allow_html=True)
st.caption("Tap **Get today's picks** to screen stocks using the 150-day moving average.")

with st.expander("Screening rules", expanded=False):
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

settings = ScreenerSettings(
    top_n=top_n,
    require_price_above_ma=require_above_ma,
    require_rising_ma=require_rising_ma,
    max_pct_above_ma=float(max_pct_above),
    min_avg_volume=int(min_volume),
)

if st.button("Get today's picks", type="primary", use_container_width=True):
    with st.spinner("Checking 150-day moving averages..."):
        st.session_state["picks"] = screen_stocks(settings)

if "picks" in st.session_state:
    picks = st.session_state["picks"]

    if not picks:
        st.warning("No stocks matched today. Try relaxing the filters above.")
    else:
        st.success(f"{len(picks)} picks for today")
        for i, pick in enumerate(picks, start=1):
            render_pick_card(pick, i)

        st.divider()
        st.subheader("Chart")
        selected = st.selectbox(
            "View price vs 150 MA",
            [p.ticker for p in picks],
            label_visibility="collapsed",
        )

        if selected:
            history = yf.Ticker(selected).history(period="1y", auto_adjust=True)
            if not history.empty:
                history["MA150"] = history["Close"].rolling(window=150).mean()
                chart_df = history[["Close", "MA150"]].dropna()
                st.line_chart(chart_df, use_container_width=True)

                pick = next(p for p in picks if p.ticker == selected)
                c1, c2 = st.columns(2)
                c1.metric("Price", f"${pick.price:.2f}")
                c2.metric("150 MA", f"${pick.ma_150:.2f}")
                c3, c4 = st.columns(2)
                c3.metric("% Above MA", f"{pick.pct_above_ma:.2f}%")
                c4.metric("MA slope", f"{pick.ma_slope_pct:.2f}%")
else:
    st.info("Open this page on your phone, tap the button above, and review today's picks.")
    st.caption(f"Screening {len(DEFAULT_TICKERS)} large-cap stocks.")

with st.expander("Use on your phone"):
    st.markdown(
        """
        **Same Wi-Fi (quick test)**  
        1. On your computer run: `./run_mobile.sh`  
        2. On your phone (same Wi-Fi), open the URL shown in the terminal.

        **From anywhere (recommended)**  
        Deploy free on [Streamlit Cloud](https://share.streamlit.io):
        - Connect this GitHub repo
        - Set main file to `stock_picker/app.py`
        - Open the link on your phone and add it to your home screen
        """
    )
