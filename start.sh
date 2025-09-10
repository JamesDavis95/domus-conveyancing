#!/usr/bin/env bash
set -euo pipefail
echo "=== Working dir ==="; pwd
echo "=== Listing ==="; ls -la
echo "=== Python version ==="; python -V
echo "=== Import check (app_rescue) ==="
python - <<'PY'
import sys, traceback
try:
    import app_rescue
    print("IMPORT OK: app_rescue")
except Exception as e:
    print("IMPORT FAIL:", e)
    traceback.print_exc()
    sys.exit(1)
PY
echo "=== Starting uvicorn ==="
exec uvicorn app_rescue:app --host 0.0.0.0 --port 8080 --proxy-headers
