#!/bin/zsh
set -e
cd "$(dirname "$0")"
echo "=== ISOMETRIC TRABZON — Trabzon Meydan ==="
command -v python3 >/dev/null || { echo "Python 3 gerekli: https://www.python.org/downloads/"; exit 1; }
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/fetch_open_data.py
python -m http.server 8000 &
SERVER_PID=$!
trap "kill $SERVER_PID 2>/dev/null || true" EXIT
sleep 1
open "http://localhost:8000" || true
echo "Harita: http://localhost:8000"
wait $SERVER_PID
