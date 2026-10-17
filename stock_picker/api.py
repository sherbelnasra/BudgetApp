"""HTTP API for the CallAlert iOS app.

Run:
  uvicorn stock_picker.api:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from stock_picker.config import OptionsAlertSettings
from stock_picker.options_alerts import demo_call_alerts, run_call_alert_screen

app = FastAPI(
    title="CallAlert API",
    description=(
        "Monthly call-option buy alerts priced $0.15–$0.20. "
        "Educational tooling — not financial advice."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/v1/call-alerts")
def call_alerts(
    top_n: int = Query(10, ge=1, le=25),
    min_premium: float = Query(0.15, ge=0.01, le=5.0),
    max_premium: float = Query(0.20, ge=0.01, le=5.0),
    demo: bool = Query(False, description="Return sample data without market calls"),
) -> dict:
    if demo:
        return demo_call_alerts()

    lo, hi = sorted((min_premium, max_premium))
    settings = OptionsAlertSettings(
        top_n=top_n,
        min_premium=lo,
        max_premium=hi,
    )
    return run_call_alert_screen(settings)


@app.get("/v1/call-alerts/demo")
def call_alerts_demo() -> dict:
    return demo_call_alerts()
