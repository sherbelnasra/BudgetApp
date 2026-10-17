"""Monthly call-option alert scanner ($0.15–$0.20 premium band).

Strategy (rules-based, not a guarantee of profit):
1. Start from liquid names with a bullish 150-MA setup (price above rising MA,
   not excessively extended).
2. Select the next standard monthly expiry (third Friday), preferring ~15–45 DTE.
3. From that chain, keep OTM calls whose mid/last price is in [$0.15, $0.20].
4. Rank by liquidity (OI/volume), tight spreads, proximity to the money, and
   underlying trend score — then emit buy-alert candidates for the iOS client.
"""

from __future__ import annotations

from calendar import monthcalendar
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Iterable

import pandas as pd
import yfinance as yf

from stock_picker.config import OptionsAlertSettings, ScreenerSettings
from stock_picker.screener import StockPick, screen_stocks


@dataclass
class CallAlert:
    ticker: str
    underlying_price: float
    contract_symbol: str
    strike: float
    expiry: str
    days_to_expiry: int
    bid: float
    ask: float
    last_price: float
    mid_price: float
    volume: int
    open_interest: int
    implied_volatility: float
    pct_otm: float
    spread_pct: float
    underlying_signal: str
    underlying_score: float
    reason: str
    score: float
    action: str = "BUY_CALL"

    def to_dict(self) -> dict:
        return asdict(self)


def _third_fridays_ahead(start: date, months: int = 4) -> set[date]:
    """Return upcoming third-Friday dates (standard monthly equity options)."""
    fridays: set[date] = set()
    year, month = start.year, start.month
    for _ in range(months + 1):
        cal = monthcalendar(year, month)
        # Third week that contains a Friday (weekday index 4).
        friday_weeks = [week[4] for week in cal if week[4] != 0]
        if len(friday_weeks) >= 3:
            fridays.add(date(year, month, friday_weeks[2]))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return fridays


def _pick_monthly_expiry(
    expiries: Iterable[str],
    settings: OptionsAlertSettings,
    today: date | None = None,
) -> str | None:
    today = today or datetime.now(timezone.utc).date()
    monthly = _third_fridays_ahead(today, months=5)
    candidates: list[tuple[int, str]] = []

    for exp_str in expiries:
        try:
            exp = date.fromisoformat(exp_str)
        except ValueError:
            continue
        dte = (exp - today).days
        if dte < settings.min_dte or dte > settings.max_dte:
            continue
        if exp not in monthly:
            continue
        # Prefer nearer monthly within the window.
        candidates.append((dte, exp_str))

    if not candidates:
        # Fallback: nearest expiry in the DTE window (covers symbols without weeklies).
        for exp_str in expiries:
            try:
                exp = date.fromisoformat(exp_str)
            except ValueError:
                continue
            dte = (exp - today).days
            if settings.min_dte <= dte <= settings.max_dte:
                candidates.append((dte, exp_str))

    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def _mid_price(bid: float, ask: float, last: float) -> float:
    if bid > 0 and ask > 0 and ask >= bid:
        return (bid + ask) / 2.0
    if last > 0:
        return last
    if ask > 0:
        return ask
    return bid


def _best_call_for_ticker(
    pick: StockPick,
    settings: OptionsAlertSettings,
) -> CallAlert | None:
    try:
        ticker = yf.Ticker(pick.ticker)
        expiries = list(ticker.options or ())
    except Exception:
        return None
    if not expiries:
        return None

    expiry = _pick_monthly_expiry(expiries, settings)
    if expiry is None:
        return None

    try:
        chain = ticker.option_chain(expiry)
        calls = chain.calls
    except Exception:
        return None
    if calls is None or calls.empty:
        return None

    today = datetime.now(timezone.utc).date()
    dte = (date.fromisoformat(expiry) - today).days
    underlying = pick.price
    best: CallAlert | None = None

    for _, row in calls.iterrows():
        strike = float(row.get("strike") or 0)
        if strike <= 0:
            continue
        if bool(row.get("inTheMoney", False)):
            continue
        if strike < underlying:  # OTM calls only
            continue

        bid = float(row.get("bid") or 0)
        ask = float(row.get("ask") or 0)
        last = float(row.get("lastPrice") or 0)
        mid = _mid_price(bid, ask, last)
        if mid < settings.min_premium or mid > settings.max_premium:
            continue

        volume = int(row.get("volume") or 0) if pd.notna(row.get("volume")) else 0
        oi = (
            int(row.get("openInterest") or 0)
            if pd.notna(row.get("openInterest"))
            else 0
        )
        if oi < settings.min_open_interest:
            continue
        if volume < settings.min_volume:
            continue

        if bid > 0 and ask > 0 and mid > 0:
            spread_pct = ((ask - bid) / mid) * 100
        else:
            spread_pct = 100.0
        if spread_pct > settings.max_spread_pct:
            continue

        iv = float(row.get("impliedVolatility") or 0)
        if iv > settings.max_iv:
            continue

        pct_otm = ((strike - underlying) / underlying) * 100
        if pct_otm > settings.max_pct_otm:
            continue

        # Prefer closer-to-money, liquid, tight-spread contracts on strong underlyings.
        proximity = max(0.0, settings.max_pct_otm - pct_otm)
        liquidity = min(oi, 5_000) / 5_000 * 3.0 + min(volume, 1_000) / 1_000 * 1.0
        spread_score = max(0.0, (settings.max_spread_pct - spread_pct) / settings.max_spread_pct) * 2.0
        score = pick.score + proximity * 0.15 + liquidity + spread_score

        reason = (
            f"{pick.signal}; monthly {expiry} ({dte}d); "
            f"${mid:.2f} mid; {pct_otm:.1f}% OTM; OI {oi}"
        )

        alert = CallAlert(
            ticker=pick.ticker,
            underlying_price=round(underlying, 2),
            contract_symbol=str(row.get("contractSymbol") or ""),
            strike=round(strike, 2),
            expiry=expiry,
            days_to_expiry=dte,
            bid=round(bid, 2),
            ask=round(ask, 2),
            last_price=round(last, 2),
            mid_price=round(mid, 2),
            volume=volume,
            open_interest=oi,
            implied_volatility=round(iv, 4),
            pct_otm=round(pct_otm, 2),
            spread_pct=round(spread_pct, 2),
            underlying_signal=pick.signal,
            underlying_score=pick.score,
            reason=reason,
            score=round(score, 2),
            action="BUY_CALL",
        )
        if best is None or alert.score > best.score:
            best = alert

    return best


def screen_call_alerts(settings: OptionsAlertSettings | None = None) -> list[CallAlert]:
    """Screen for monthly call buy alerts in the configured premium band."""
    settings = settings or OptionsAlertSettings()
    screener = ScreenerSettings(
        tickers=settings.tickers,
        top_n=max(settings.top_n * 3, 20),
        require_price_above_ma=settings.require_bullish_underlying,
        require_rising_ma=settings.require_bullish_underlying,
        max_pct_above_ma=settings.max_pct_above_ma,
        min_avg_volume=settings.min_avg_volume,
    )
    picks = screen_stocks(screener)
    alerts: list[CallAlert] = []

    for pick in picks:
        alert = _best_call_for_ticker(pick, settings)
        if alert is not None:
            alerts.append(alert)

    alerts.sort(key=lambda a: a.score, reverse=True)
    return alerts[: settings.top_n]


def run_call_alert_screen(settings: OptionsAlertSettings | None = None) -> dict:
    """Run the call-alert screen and return JSON-serializable results."""
    settings = settings or OptionsAlertSettings()
    alerts = screen_call_alerts(settings)
    now = datetime.now(timezone.utc)
    return {
        "generated_at": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "disclaimer": (
            "Educational alerts only — not financial advice. "
            "Cheap OTM calls can expire worthless. Size risk carefully."
        ),
        "criteria": {
            "min_premium": settings.min_premium,
            "max_premium": settings.max_premium,
            "min_dte": settings.min_dte,
            "max_dte": settings.max_dte,
            "monthly_expiry": True,
            "otm_only": True,
            "bullish_150_ma": settings.require_bullish_underlying,
            "min_open_interest": settings.min_open_interest,
            "max_spread_pct": settings.max_spread_pct,
        },
        "universe_size": len(settings.tickers),
        "alerts_count": len(alerts),
        "alerts": [a.to_dict() for a in alerts],
        "next_poll_seconds": settings.poll_seconds,
    }


def demo_call_alerts() -> dict:
    """Deterministic sample payload for iOS UI / offline demos."""
    today = datetime.now(timezone.utc).date()
    # Next third Friday roughly a month out for demo display.
    monthly = sorted(_third_fridays_ahead(today, months=2))
    expiry = (monthly[1] if len(monthly) > 1 else today + timedelta(days=30)).isoformat()
    dte = (date.fromisoformat(expiry) - today).days
    sample = CallAlert(
        ticker="DEMO",
        underlying_price=100.0,
        contract_symbol=f"DEMO{expiry.replace('-', '')[2:]}C00120000",
        strike=120.0,
        expiry=expiry,
        days_to_expiry=dte,
        bid=0.15,
        ask=0.19,
        last_price=0.17,
        mid_price=0.17,
        volume=120,
        open_interest=850,
        implied_volatility=0.42,
        pct_otm=20.0,
        spread_pct=23.5,
        underlying_signal="Above rising 150 MA",
        underlying_score=4.2,
        reason=f"Demo alert; monthly {expiry}; $0.17 mid; 20% OTM",
        score=8.5,
        action="BUY_CALL",
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date": today.isoformat(),
        "disclaimer": (
            "DEMO DATA — not a live market signal. "
            "Educational alerts only — not financial advice."
        ),
        "criteria": {
            "min_premium": 0.15,
            "max_premium": 0.20,
            "min_dte": 15,
            "max_dte": 45,
            "monthly_expiry": True,
            "otm_only": True,
            "bullish_150_ma": True,
        },
        "universe_size": 1,
        "alerts_count": 1,
        "alerts": [sample.to_dict()],
        "next_poll_seconds": 300,
        "demo": True,
    }
