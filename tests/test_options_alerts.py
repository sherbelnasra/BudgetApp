"""Unit tests for monthly call-alert helpers (no live market required)."""

from datetime import date

from stock_picker.config import OptionsAlertSettings
from stock_picker.options_alerts import (
    _mid_price,
    _pick_monthly_expiry,
    _third_fridays_ahead,
    demo_call_alerts,
)


def test_third_friday_oct_2026():
    fridays = _third_fridays_ahead(date(2026, 10, 1), months=1)
    assert date(2026, 10, 16) in fridays


def test_pick_monthly_expiry_prefers_third_friday():
    settings = OptionsAlertSettings(min_dte=15, max_dte=45)
    # Include a weekly and the October 2026 monthly third Friday.
    expiries = ["2026-10-09", "2026-10-16", "2026-10-23", "2026-11-20"]
    chosen = _pick_monthly_expiry(expiries, settings, today=date(2026, 10, 1))
    assert chosen == "2026-10-16"


def test_mid_price_uses_bid_ask():
    assert abs(_mid_price(0.15, 0.19, 0.50) - 0.17) < 1e-9


def test_demo_payload_shape():
    payload = demo_call_alerts()
    assert payload["alerts_count"] == 1
    alert = payload["alerts"][0]
    assert 0.15 <= alert["mid_price"] <= 0.20
    assert alert["action"] == "BUY_CALL"
    assert "disclaimer" in payload
