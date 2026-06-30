"""Stock screener using the 150-day moving average."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

from stock_picker.config import ScreenerSettings


@dataclass
class StockPick:
    ticker: str
    price: float
    ma_150: float
    pct_above_ma: float
    ma_slope_pct: float
    avg_volume: int
    signal: str
    score: float

    def to_dict(self) -> dict:
        return asdict(self)


def _fetch_history(ticker: str) -> pd.DataFrame | None:
    try:
        data = yf.Ticker(ticker).history(period="1y", auto_adjust=True)
        if data.empty or "Close" not in data.columns:
            return None
        return data
    except Exception:
        return None


def _analyze_ticker(ticker: str, settings: ScreenerSettings) -> StockPick | None:
    history = _fetch_history(ticker)
    if history is None or len(history) < settings.ma_period + 5:
        return None

    close = history["Close"]
    volume = history["Volume"]

    ma = close.rolling(window=settings.ma_period).mean()
    current_price = float(close.iloc[-1])
    current_ma = float(ma.iloc[-1])

    if pd.isna(current_ma) or current_ma <= 0:
        return None

    pct_above_ma = ((current_price - current_ma) / current_ma) * 100

    slope_idx = -1 - min(20, settings.ma_period // 7)
    prior_ma = float(ma.iloc[slope_idx])
    ma_slope_pct = ((current_ma - prior_ma) / prior_ma) * 100 if prior_ma > 0 else 0.0

    avg_volume = int(volume.tail(20).mean())

    if settings.require_price_above_ma and current_price <= current_ma:
        return None
    if settings.require_rising_ma and ma_slope_pct <= 0:
        return None
    if pct_above_ma > settings.max_pct_above_ma:
        return None
    if avg_volume < settings.min_avg_volume:
        return None

    # Higher score = stronger but not overextended setup above rising 150 MA.
    score = (pct_above_ma * 0.4) + (ma_slope_pct * 0.4) + (min(avg_volume, 5_000_000) / 5_000_000 * 2.0)

    if current_price > current_ma and ma_slope_pct > 0:
        signal = "Above rising 150 MA"
    elif current_price > current_ma:
        signal = "Above 150 MA"
    else:
        signal = "Below 150 MA"

    return StockPick(
        ticker=ticker,
        price=round(current_price, 2),
        ma_150=round(current_ma, 2),
        pct_above_ma=round(pct_above_ma, 2),
        ma_slope_pct=round(ma_slope_pct, 2),
        avg_volume=avg_volume,
        signal=signal,
        score=round(score, 2),
    )


def screen_stocks(settings: ScreenerSettings | None = None) -> list[StockPick]:
    """Screen tickers and return ranked daily investment candidates."""
    settings = settings or ScreenerSettings()
    picks: list[StockPick] = []

    for ticker in settings.tickers:
        result = _analyze_ticker(ticker, settings)
        if result is not None:
            picks.append(result)

    picks.sort(key=lambda p: p.score, reverse=True)
    return picks[: settings.top_n]


def picks_to_dataframe(picks: list[StockPick]) -> pd.DataFrame:
    if not picks:
        return pd.DataFrame(
            columns=[
                "ticker", "price", "ma_150", "pct_above_ma",
                "ma_slope_pct", "avg_volume", "signal", "score",
            ]
        )
    return pd.DataFrame([p.to_dict() for p in picks])


def run_daily_screen(settings: ScreenerSettings | None = None) -> dict:
    """Run the daily screen and return results with metadata."""
    settings = settings or ScreenerSettings()
    picks = screen_stocks(settings)
    return {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "criteria": {
            "ma_period": settings.ma_period,
            "price_above_ma": settings.require_price_above_ma,
            "rising_ma": settings.require_rising_ma,
            "max_pct_above_ma": settings.max_pct_above_ma,
        },
        "universe_size": len(settings.tickers),
        "picks_count": len(picks),
        "picks": [p.to_dict() for p in picks],
    }
