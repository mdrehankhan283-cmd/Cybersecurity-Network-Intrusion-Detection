#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -f .venv/bin/python ]; then python3 -m venv .venv; fi
if [ ! -f .venv/netguard-ready ]; then
  .venv/bin/python -m pip install -r requirements.txt
  touch .venv/netguard-ready
fi
exec .venv/bin/python app.py
