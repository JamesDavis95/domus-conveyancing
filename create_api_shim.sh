#!/usr/bin/env bash
set -euo pipefail

echo ">> Searching for a FastAPI APIRouter named 'router'..."
# Find Python files that define an APIRouter and a symbol called router
matches=$(find . -type f -name "*.py" -maxdepth 3 -print0 \
  | xargs -0 grep -El 'APIRouter\(|from fastapi import APIRouter' || true)

cand=""
for f in $matches; do
  if grep -Eq '(^|[^a-zA-Z0-9_])router[[:space:]]*=' "$f"; then
    cand="$f"
    break
  fi
done

if [ -z "${cand}" ]; then
  echo "!! Could not locate a file that defines 'router = APIRouter(...)'."
  echo "   Please tell me which file holds your main router, or paste 'ls -R' here."
  exit 1
fi

# Turn the file path into a Python module path (strip leading ./, remove .py, replace / with .)
mod="${cand#./}"
mod="${mod%.py}"
mod="${mod//\//.}"

echo ">> Found router candidate: $cand  (module: $mod)"
echo ">> Writing api.py shim that re-exports 'router' from $mod"

cat > api.py <<PY
# Auto-generated shim so 'from api import router' works
try:
    from ${mod} import router  # re-export
except Exception as e:
    # Fail loud with helpful message so we know what to fix
    raise ImportError(f"Failed to import 'router' from module '${mod}': {e}")
PY

echo ">> Created api.py shim:"
sed -n '1,120p' api.py
