#!/usr/bin/env bash
set -euo pipefail

echo "[alembic-predeploy] upgrade head..."
alembic upgrade head && exit 0

echo "[alembic-predeploy] upgrade failed; inspecting..."
# Empty DB? stamp base then upgrade.
if alembic current 2>&1 | grep -qi "No such table"; then
  echo "[alembic-predeploy] empty DB -> alembic stamp base; upgrade head"
  alembic stamp base || true
  alembic upgrade head
  exit 0
fi

echo "[alembic-predeploy] Non-empty DB and upgrade failed (broken chain). Aborting."
exit 1