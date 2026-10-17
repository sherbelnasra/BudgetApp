# CallAlert (iOS)

SwiftUI client that polls the CallAlert API and fires a **local notification** when a new monthly call in the **$0.15–$0.20** band is ranked as a buy alert.

**Fastest way to try on your phone today:** use the web home-screen app (icon included):

```bash
./run_phone.sh
# iPhone Safari → open the printed URL → Share → Add to Home Screen
```

See also `web/callalert/` — same icon as the native AppIcon asset.

## What you get

- Feed of ranked `BUY_CALL` alerts
- Local push when a new contract appears
- Settings for API URL + demo mode
- Premium band fixed to $0.15–$0.20, monthly (3rd Friday) expiry

## 1. Start the API (Mac / Linux)

From the repo root:

```bash
pip install -r requirements.txt
uvicorn stock_picker.api:app --host 0.0.0.0 --port 8000
```

Quick checks:

```bash
curl 'http://127.0.0.1:8000/v1/call-alerts/demo'
python -m stock_picker.cli --mode calls --demo
python -m stock_picker.cli --mode calls --top-n 5
```

## 2. Open the iOS app in Xcode

**Option A — XcodeGen (recommended)**

```bash
brew install xcodegen
cd ios/CallAlert
xcodegen generate
open CallAlert.xcodeproj
```

**Option B — manual**

1. Xcode → File → New → Project → iOS App (SwiftUI, Swift)
2. Name it `CallAlert`
3. Replace the generated sources with the files in this folder
4. Set the target’s Info.plist to `Info.plist` (allows local HTTP)

Run on a Simulator first with **Use demo data** enabled in Settings.

## 3. Point the phone at your API

| Environment | API base URL |
|---|---|
| Simulator | `http://127.0.0.1:8000` |
| Physical iPhone | `http://<your-computer-lan-ip>:8000` |

Allow notifications when prompted. Disable demo mode for live Yahoo Finance–backed scans.

## Strategy (rules-based)

1. Underlying must clear a **rising 150-day MA** (not too extended)
2. Take the next **monthly** expiry (3rd Friday, ~15–45 DTE)
3. Keep **OTM calls** whose mid/last price is **$0.15–$0.20**
4. Filter thin OI / absurd spreads / extreme IV
5. Rank and notify

**Not financial advice.** Cheap OTM calls often expire worthless — treat alerts as research prompts, not orders.

## Background notes

- Local notifications fire when the app is open / recently active and polling.
- True silent push (APNs) needs a hosted push service; this MVP uses local notifications after each poll.
- Live scans hit Yahoo Finance via `yfinance` and can take 1–3 minutes for the full universe.
