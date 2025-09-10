#!/usr/bin/env bash
set -euo pipefail

# Find the python file that both defines an APIRouter AND mentions "/api/process"
cand="$(grep -R --include="*.py" -nE 'APIRouter' . \
  | cut -d: -f1 | sort -u \
  | while read -r f; do
      if grep -qE '/api/process' "$f"; then echo "$f"; fi
    done | head -n1)"

# Fallback: find any router that registers '/api/' paths
if [ -z "${cand}" ]; then
  cand="$(grep -R --include="*.py" -nE 'APIRouter' . \
    | cut -d: -f1 | sort -u \
    | while read -r f; do
        if grep -qE '/api/' "$f"; then echo "$f"; fi
      done | head -n1)"
fi

if [ -z "${cand}" ]; then
  echo "!! Could not find the API router that defines /api/process."
  echo "Here are all files with APIRouter:"
  grep -R --include="*.py" -nE 'APIRouter' . || true
  exit 1
fi

mod="${cand#./}"; mod="${mod%.py}"; mod="${mod//\//.}"
echo ">> Using ${cand}  (module: ${mod})"

cat > api.py <<PY
# Auto-generated shim so 'from api import router' works
from ${mod} import router  # re-export
PY
echo ">> Wrote api.py shim:"
sed -n '1,80p' api.py
