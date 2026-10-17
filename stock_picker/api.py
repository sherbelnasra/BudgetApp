"""HTTP API + phone PWA for CallAlert.

Run:
  uvicorn stock_picker.api:app --host 0.0.0.0 --port 8000

Then open http://<lan-ip>:8000 on your phone and Add to Home Screen.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from stock_picker.config import OptionsAlertSettings
from stock_picker.options_alerts import demo_call_alerts, run_call_alert_screen

WEB_ROOT = Path(__file__).resolve().parents[1] / "web" / "callalert"

app = FastAPI(
    title="CallAlert API",
    description=(
        "Monthly call-option buy alerts priced $0.15–$0.20. "
        "Educational tooling — not financial advice."
    ),
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if WEB_ROOT.is_dir():
    app.mount("/app", StaticFiles(directory=str(WEB_ROOT), html=True), name="callalert-web")


@app.get("/")
def root() -> RedirectResponse:
    """Phone users land on the installable CallAlert PWA."""
    return RedirectResponse(url="/app/")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "pwa": WEB_ROOT.is_dir()}


@app.get("/apple-touch-icon.png")
def apple_touch_icon() -> FileResponse:
    return FileResponse(WEB_ROOT / "icons" / "apple-touch-icon.png")


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
