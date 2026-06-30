#!/usr/bin/env bash
# Run the stock picker so your phone can open it on the same Wi-Fi network.
set -euo pipefail

HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
PORT="${PORT:-8501}"

echo ""
echo "Starting Daily Stock Picker..."
echo "On this computer:  http://localhost:${PORT}"
if [ -n "${HOST_IP}" ]; then
  echo "On your phone:     http://${HOST_IP}:${PORT}"
  echo "(Phone must be on the same Wi-Fi network)"
fi
echo ""

exec streamlit run stock_picker/app.py --server.port "${PORT}"
