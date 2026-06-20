#!/bin/sh
set -e
PORT="${PORT:-8000}"
exec python -m uvicorn web.backend.main:app --host 0.0.0.0 --port "$PORT"
