#!/usr/bin/env bash
# Start CallAlert so you can open it on your phone and Add to Home Screen.
set -euo pipefail

PORT="${PORT:-8000}"
HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"

echo ""
echo "Starting CallAlert (API + phone icon app)..."
echo "On this computer:  http://localhost:${PORT}/app/"
if [ -n "${HOST_IP}" ]; then
  echo "On your phone:     http://${HOST_IP}:${PORT}/app/"
  echo "(Phone must be on the same Wi-Fi as this computer)"
fi
echo ""
echo "iPhone: Safari → Share → Add to Home Screen → Add"
echo "Android: Chrome → Install app / Add to Home screen"
echo ""

exec python3 -m uvicorn stock_picker.api:app --host 0.0.0.0 --port "${PORT}"
