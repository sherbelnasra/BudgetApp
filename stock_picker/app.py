"""Streamlit dashboard for stock scalping entries with a 5% profit target."""

from __future__ import annotations

import streamlit as st
import yfinance as yf

from stock_picker.config import DEFAULT_TICKERS, ScalpSettings, ScreenerSettings
from stock_picker.scalper import entries_to_dataframe, screen_scalps
from stock_picker.screener import picks_to_dataframe, screen_stocks

st.set_page_config(
    page_title="Scalp Desk — 5% Targets",
    page_icon="⚡",
    layout="wide",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&family=JetBrains+Mono:wght@500&display=swap');

    :root {
        --ink: #0f1a14;
        --mint: #1fa97a;
        --mint-dim: #147a58;
        --warn: #c45c26;
        --panel: rgba(15, 26, 20, 0.04);
        --line: rgba(15, 26, 20, 0.12);
    }

    .stApp {
        background:
            radial-gradient(1200px 600px at 10% -10%, #d8f3e7 0%, transparent 55%),
            radial-gradient(900px 500px at 100% 0%, #f3e6d8 0%, transparent 50%),
            linear-gradient(180deg, #f7faf8 0%, #eef3f0 100%);
        color: var(--ink);
        font-family: 'DM Sans', sans-serif;
    }

    h1, h2, h3 { font-family: 'DM Sans', sans-serif !important; letter-spacing: -0.02em; }

    .hero-brand {
        font-size: clamp(2.4rem, 5vw, 3.6rem);
        font-weight: 700;
        line-height: 1.05;
        margin: 0 0 0.35rem 0;
        color: var(--ink);
    }
    .hero-sub {
        font-size: 1.05rem;
        color: rgba(15, 26, 20, 0.72);
        max-width: 38rem;
        margin-bottom: 1.25rem;
    }
    .pill {
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        padding: 0.35rem 0.65rem;
        border: 1px solid var(--line);
        background: var(--panel);
        margin-right: 0.4rem;
        margin-bottom: 0.75rem;
    }
    .metric-strip {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.75rem;
        margin: 1rem 0 1.5rem 0;
    }
    .metric-cell {
        border-top: 2px solid var(--mint);
        padding: 0.75rem 0.1rem;
    }
    .metric-cell span {
        display: block;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: rgba(15, 26, 20, 0.55);
    }
    .metric-cell strong {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.35rem;
        color: var(--ink);
    }
    .disclaimer {
        font-size: 0.8rem;
        color: rgba(15, 26, 20, 0.55);
        border-top: 1px solid var(--line);
        padding-top: 0.75rem;
        margin-top: 1.5rem;
    }
    @media (max-width: 768px) {
        .metric-strip { grid-template-columns: 1fr 1fr; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="pill">SCALP DESK</div>', unsafe_allow_html=True)
st.markdown('<p class="hero-brand">Scalp Desk</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-sub">Live entries for liquid stocks with enough volatility '
    "to chase a <strong>5% profit target</strong> — entry, stop, and R:R in one pass.</p>",
    unsafe_allow_html=True,
)

tab_scalp, tab_ma = st.tabs(["5% Scalp Entries", "150 MA Picks"])

with st.sidebar:
    st.header("Scalp filters")
    top_n = st.slider("Max entries", min_value=5, max_value=30, value=15)
    target_pct = st.slider("Profit target %", min_value=3.0, max_value=8.0, value=5.0, step=0.5)
    stop_pct = st.slider("Stop loss %", min_value=1.0, max_value=4.0, value=2.0, step=0.5)
    min_atr = st.slider("Min ATR % (volatility)", min_value=1.5, max_value=6.0, value=2.5, step=0.25)
    min_volume = st.number_input(
        "Min avg daily volume",
        min_value=250_000,
        max_value=10_000_000,
        value=1_000_000,
        step=250_000,
    )
    long_only = st.checkbox("Long setups only", value=True)
    actionable_only = st.checkbox("Hide watchlist / weak setups", value=True)

    st.divider()
    st.markdown(
        """
        **Entry logic**
        1. Filter for ATR large enough that **5%** is reachable
        2. Require liquid average volume
        3. Classify setup (breakout, pullback, continuation…)
        4. Set **entry / target / stop** and rank by score
        """
    )

scalp_settings = ScalpSettings(
    top_n=top_n,
    target_pct=float(target_pct),
    stop_pct=float(stop_pct),
    min_atr_pct=float(min_atr),
    min_avg_volume=int(min_volume),
    long_only=long_only,
    require_actionable=actionable_only,
)

with tab_scalp:
    col_refresh, col_status = st.columns([1, 3])
    with col_refresh:
        refresh = st.button("Refresh scan", type="primary", use_container_width=True)

    settings_key = (
        scalp_settings.top_n,
        scalp_settings.target_pct,
        scalp_settings.stop_pct,
        scalp_settings.min_atr_pct,
        scalp_settings.min_avg_volume,
        scalp_settings.long_only,
        scalp_settings.require_actionable,
    )
    needs_scan = (
        refresh
        or "scalp_entries" not in st.session_state
        or st.session_state.get("scalp_settings_key") != settings_key
    )

    if needs_scan:
        with st.spinner("Screening for volatile 5% scalp setups..."):
            entries = screen_scalps(scalp_settings)
            st.session_state["scalp_entries"] = entries
            st.session_state["scalp_settings"] = scalp_settings
            st.session_state["scalp_settings_key"] = settings_key

    if "scalp_entries" in st.session_state:
        entries = st.session_state["scalp_entries"]
        settings = st.session_state["scalp_settings"]

        if not entries:
            st.warning("No scalp setups matched. Lower Min ATR % or turn off actionable-only.")
        else:
            longs = sum(1 for e in entries if e.bias == "Long")
            shorts = sum(1 for e in entries if e.bias == "Short")
            avg_rr = sum(e.risk_reward for e in entries) / len(entries)
            top = entries[0]

            st.markdown(
                f"""
                <div class="metric-strip">
                  <div class="metric-cell"><span>Entries</span><strong>{len(entries)}</strong></div>
                  <div class="metric-cell"><span>Long / Short</span><strong>{longs} / {shorts}</strong></div>
                  <div class="metric-cell"><span>Avg R:R</span><strong>{avg_rr:.1f}x</strong></div>
                  <div class="metric-cell"><span>Top ticker</span><strong>{top.ticker}</strong></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            df = entries_to_dataframe(entries)
            display = df[
                [
                    "ticker",
                    "bias",
                    "setup",
                    "entry",
                    "target",
                    "stop",
                    "reward_pct",
                    "risk_pct",
                    "risk_reward",
                    "atr_pct",
                    "volume_ratio",
                    "rsi",
                    "score",
                ]
            ].rename(
                columns={
                    "ticker": "Ticker",
                    "bias": "Bias",
                    "setup": "Setup",
                    "entry": "Entry ($)",
                    "target": "Target ($)",
                    "stop": "Stop ($)",
                    "reward_pct": "Target %",
                    "risk_pct": "Stop %",
                    "risk_reward": "R:R",
                    "atr_pct": "ATR %",
                    "volume_ratio": "Vol ×",
                    "rsi": "RSI",
                    "score": "Score",
                }
            )

            st.subheader("Ranked scalp entries")
            st.dataframe(
                display.style.format(
                    {
                        "Entry ($)": "${:.2f}",
                        "Target ($)": "${:.2f}",
                        "Stop ($)": "${:.2f}",
                        "Target %": "{:.1f}%",
                        "Stop %": "{:.1f}%",
                        "R:R": "{:.2f}",
                        "ATR %": "{:.2f}%",
                        "Vol ×": "{:.2f}",
                        "RSI": "{:.1f}",
                        "Score": "{:.2f}",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

            st.subheader("Trade card")
            selected = st.selectbox("Inspect entry", [e.ticker for e in entries])
            pick = next(e for e in entries if e.ticker == selected)

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Entry", f"${pick.entry:.2f}")
            c2.metric("Target (+{:.0f}%)".format(pick.reward_pct), f"${pick.target:.2f}")
            c3.metric("Stop (−{:.0f}%)".format(pick.risk_pct) if pick.bias == "Long" else f"Stop (+{pick.risk_pct:.0f}%)", f"${pick.stop:.2f}")
            c4.metric("R:R", f"{pick.risk_reward:.2f}x")
            c5.metric("ATR", f"{pick.atr_pct:.2f}%")

            st.info(f"**{pick.setup}** · {pick.bias} — {pick.notes}")

            history = yf.Ticker(selected).history(period="3mo", auto_adjust=True)
            if not history.empty:
                close = history["Close"]
                chart = history[["Close"]].copy()
                chart["EMA9"] = close.ewm(span=9, adjust=False).mean()
                chart["EMA21"] = close.ewm(span=21, adjust=False).mean()
                chart["Target"] = pick.target
                chart["Stop"] = pick.stop
                st.line_chart(chart.dropna(), use_container_width=True)

with tab_ma:
    st.caption("Legacy daily picker — stocks above a rising 150-day moving average.")
    ma_top = st.slider("MA picks", min_value=3, max_value=20, value=10, key="ma_top")
    if st.button("Run 150 MA screen", use_container_width=True):
        with st.spinner("Screening against the 150-day MA..."):
            picks = screen_stocks(ScreenerSettings(top_n=ma_top))
            st.session_state["ma_picks"] = picks

    if "ma_picks" in st.session_state:
        picks = st.session_state["ma_picks"]
        if not picks:
            st.warning("No MA picks today.")
        else:
            df = picks_to_dataframe(picks).rename(
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
            st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown(
    '<p class="disclaimer">Educational screening only — not financial advice. '
    "5% stock moves are aggressive; size risk carefully and confirm with live order flow.</p>",
    unsafe_allow_html=True,
)
