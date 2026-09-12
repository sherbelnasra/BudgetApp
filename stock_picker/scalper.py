"""Scalping screener: find liquid stocks with ~5% profit-target setups."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yfinance as yf

from stock_picker.config import ScalpSettings


@dataclass
class ScalpEntry:
    ticker: str
    price: float
    entry: float
    target: float
    stop: float
    reward_pct: float
    risk_pct: float
    risk_reward: float
    atr_pct: float
    day_range_pct: float
    volume_ratio: float
    rsi: float
    setup: str
    bias: str
    score: float
    notes: str

    def to_dict(self) -> dict:
        return asdict(self)


def _true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    ranges = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    )
    return ranges.max(axis=1)


def _rsi(close: pd.Series, period: int = 14) -> float:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    value = float(rsi.iloc[-1])
    return value if not pd.isna(value) else 50.0


def _fetch_history(ticker: str, period: str = "3mo") -> pd.DataFrame | None:
    try:
        data = yf.Ticker(ticker).history(period=period, auto_adjust=True)
        if data.empty or len(data) < 25:
            return None
        required = {"Open", "High", "Low", "Close", "Volume"}
        if not required.issubset(data.columns):
            return None
        return data
    except Exception:
        return None


def _fetch_universe(tickers: list[str], period: str = "3mo") -> dict[str, pd.DataFrame]:
    """Batch-download OHLCV for the universe; fall back per-ticker on failure."""
    histories: dict[str, pd.DataFrame] = {}
    if not tickers:
        return histories

    try:
        raw = yf.download(
            tickers=tickers,
            period=period,
            group_by="ticker",
            auto_adjust=True,
            threads=True,
            progress=False,
        )
    except Exception:
        raw = None

    if raw is not None and not raw.empty:
        if len(tickers) == 1:
            ticker = tickers[0]
            frame = raw.copy()
            if len(frame) >= 25 and {"Open", "High", "Low", "Close", "Volume"}.issubset(frame.columns):
                histories[ticker] = frame
            return histories

        for ticker in tickers:
            try:
                if ticker not in raw.columns.get_level_values(0):
                    continue
                frame = raw[ticker].dropna(how="all")
                if len(frame) < 25:
                    continue
                if not {"Open", "High", "Low", "Close", "Volume"}.issubset(frame.columns):
                    continue
                histories[ticker] = frame
            except Exception:
                continue

    missing = [t for t in tickers if t not in histories]
    for ticker in missing:
        frame = _fetch_history(ticker, period=period)
        if frame is not None:
            histories[ticker] = frame
    return histories


def _classify_setup(
    *,
    price: float,
    ema9: float,
    ema21: float,
    recent_high: float,
    recent_low: float,
    rsi: float,
    volume_ratio: float,
    day_change_pct: float,
) -> tuple[str, str, str]:
    """Return (setup, bias, notes)."""
    near_high = price >= recent_high * 0.985
    near_low = price <= recent_low * 1.015
    uptrend = ema9 > ema21 and price > ema21
    downtrend = ema9 < ema21 and price < ema21

    if uptrend and near_high and volume_ratio >= 1.3 and rsi >= 55:
        return (
            "Momentum breakout",
            "Long",
            "Price pressing 10-day highs with rising volume — scalp toward +5%.",
        )
    if uptrend and rsi <= 45 and volume_ratio >= 1.0:
        return (
            "Pullback long",
            "Long",
            "Trend intact; pullback cooling RSI — look for bounce to +5% target.",
        )
    if uptrend and 45 < rsi < 65 and day_change_pct > 0:
        return (
            "Trend continuation",
            "Long",
            "Above short EMAs with constructive momentum for a 5% swing scalp.",
        )
    if downtrend and near_low and volume_ratio >= 1.3 and rsi <= 45:
        return (
            "Breakdown short",
            "Short",
            "Selling pressure near lows — short scalp toward −5% target.",
        )
    if downtrend and rsi >= 55:
        return (
            "Rally short",
            "Short",
            "Downtrend bounce into resistance — short scalp for 5% move.",
        )
    if volume_ratio >= 1.5 and abs(day_change_pct) >= 1.5:
        bias = "Long" if day_change_pct > 0 else "Short"
        return (
            "Volatility expansion",
            bias,
            "Elevated volume and range — room for a 5% scalp if direction holds.",
        )
    return (
        "Watchlist",
        "Long" if uptrend else "Neutral",
        "Volatile enough for 5%, but wait for a cleaner trigger.",
    )


def _analyze_frame(ticker: str, history: pd.DataFrame, settings: ScalpSettings) -> ScalpEntry | None:
    if history is None or len(history) < 25:
        return None

    close = history["Close"]
    high = history["High"]
    low = history["Low"]
    volume = history["Volume"]

    price = float(close.iloc[-1])
    if price <= 0 or pd.isna(price):
        return None

    tr = _true_range(high, low, close)
    atr = float(tr.tail(settings.atr_period).mean())
    if pd.isna(atr) or atr <= 0:
        return None
    atr_pct = (atr / price) * 100

    # Need enough daily volatility that a 5% move is realistic (~1.2–2× ATR).
    if atr_pct < settings.min_atr_pct:
        return None

    avg_vol = float(volume.tail(20).mean())
    if pd.isna(avg_vol) or avg_vol < settings.min_avg_volume:
        return None

    today_vol = float(volume.iloc[-1])
    volume_ratio = today_vol / avg_vol if avg_vol > 0 else 0.0

    day_high = float(high.iloc[-1])
    day_low = float(low.iloc[-1])
    day_range_pct = ((day_high - day_low) / price) * 100 if price else 0.0

    prev_close = float(close.iloc[-2]) if len(close) > 1 else price
    day_change_pct = ((price - prev_close) / prev_close) * 100 if prev_close else 0.0

    ema9 = float(close.ewm(span=9, adjust=False).mean().iloc[-1])
    ema21 = float(close.ewm(span=21, adjust=False).mean().iloc[-1])
    recent_high = float(high.tail(10).max())
    recent_low = float(low.tail(10).min())
    rsi = _rsi(close, settings.rsi_period)

    setup, bias, notes = _classify_setup(
        price=price,
        ema9=ema9,
        ema21=ema21,
        recent_high=recent_high,
        recent_low=recent_low,
        rsi=rsi,
        volume_ratio=volume_ratio,
        day_change_pct=day_change_pct,
    )

    if settings.long_only and bias == "Short":
        return None
    if settings.require_actionable and setup == "Watchlist":
        return None

    reward_pct = settings.target_pct
    risk_pct = settings.stop_pct

    if bias == "Short":
        entry = round(price, 2)
        target = round(price * (1 - reward_pct / 100), 2)
        stop = round(price * (1 + risk_pct / 100), 2)
    else:
        entry = round(price, 2)
        target = round(price * (1 + reward_pct / 100), 2)
        stop = round(price * (1 - risk_pct / 100), 2)

    risk_reward = round(reward_pct / risk_pct, 2) if risk_pct else 0.0

    # Score favors: ATR room for 5%, volume surge, clean setup, RSI not extreme.
    atr_room = min(atr_pct / settings.target_pct, 1.5) * 3.0
    vol_score = min(volume_ratio, 3.0) * 1.5
    setup_bonus = {
        "Momentum breakout": 3.0,
        "Pullback long": 2.5,
        "Trend continuation": 2.0,
        "Breakdown short": 2.5,
        "Rally short": 2.0,
        "Volatility expansion": 1.5,
        "Watchlist": 0.5,
    }.get(setup, 1.0)
    rsi_penalty = 0.0
    if bias == "Long" and rsi > 78:
        rsi_penalty = 1.5
    elif bias == "Short" and rsi < 22:
        rsi_penalty = 1.5
    range_score = min(day_range_pct / 3.0, 1.5)

    score = atr_room + vol_score + setup_bonus + range_score - rsi_penalty

    return ScalpEntry(
        ticker=ticker,
        price=round(price, 2),
        entry=entry,
        target=target,
        stop=stop,
        reward_pct=reward_pct,
        risk_pct=risk_pct,
        risk_reward=risk_reward,
        atr_pct=round(atr_pct, 2),
        day_range_pct=round(day_range_pct, 2),
        volume_ratio=round(volume_ratio, 2),
        rsi=round(rsi, 1),
        setup=setup,
        bias=bias,
        score=round(score, 2),
        notes=notes,
    )


def _analyze_ticker(ticker: str, settings: ScalpSettings) -> ScalpEntry | None:
    history = _fetch_history(ticker)
    if history is None:
        return None
    return _analyze_frame(ticker, history, settings)


def screen_scalps(settings: ScalpSettings | None = None) -> list[ScalpEntry]:
    """Screen tickers for scalping entries with a fixed profit target."""
    settings = settings or ScalpSettings()
    histories = _fetch_universe(settings.tickers)
    entries: list[ScalpEntry] = []

    for ticker, history in histories.items():
        result = _analyze_frame(ticker, history, settings)
        if result is not None:
            entries.append(result)

    entries.sort(key=lambda e: e.score, reverse=True)
    return entries[: settings.top_n]


def entries_to_dataframe(entries: list[ScalpEntry]) -> pd.DataFrame:
    if not entries:
        return pd.DataFrame(
            columns=[
                "ticker",
                "price",
                "entry",
                "target",
                "stop",
                "reward_pct",
                "risk_pct",
                "risk_reward",
                "atr_pct",
                "day_range_pct",
                "volume_ratio",
                "rsi",
                "setup",
                "bias",
                "score",
                "notes",
            ]
        )
    return pd.DataFrame([e.to_dict() for e in entries])


def run_scalp_screen(settings: ScalpSettings | None = None) -> dict:
    """Run the scalping screen and return results with metadata."""
    settings = settings or ScalpSettings()
    entries = screen_scalps(settings)
    return {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "criteria": {
            "target_pct": settings.target_pct,
            "stop_pct": settings.stop_pct,
            "min_atr_pct": settings.min_atr_pct,
            "min_avg_volume": settings.min_avg_volume,
            "long_only": settings.long_only,
            "require_actionable": settings.require_actionable,
        },
        "universe_size": len(settings.tickers),
        "entries_count": len(entries),
        "entries": [e.to_dict() for e in entries],
    }
