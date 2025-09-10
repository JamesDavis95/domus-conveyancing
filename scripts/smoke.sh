set -euo pipefail
BASE=${1:-http://localhost:8000}
curl -sf "$BASE/health" >/dev/null
curl -sf "$BASE/metrics" >/dev/null
curl -sf -X POST "$BASE/la/matters/ingest" >/dev/null
REF=$(curl -sf "$BASE/la/matters/list" | jq -r '.matters[0].ref')
OUT=$(curl -sf -X POST "$BASE/api/process" -F "ref=$REF" -F 'llc1_text=Conservation Area.' -F 'con29_text=Abutting highway adopted: no.')
JID=$(echo "$OUT" | jq -r .job_id)
if [ "$JID" != "null" ]; then
  until [ "$(curl -sf "$BASE/jobs/$JID/status" | jq -r .status)" = "finished" ]; do sleep 0.5; done
fi
MID=$(curl -sf "$BASE/la/matters/list" | jq -r '.matters[0].id')
curl -sf "$BASE/la/matters/$MID/detail" | jq -e '.risks|length>=1' >/dev/null
echo "SMOKE OK"
