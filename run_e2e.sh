#!/usr/bin/env bash
set -euo pipefail

docker-compose up -d --build api

for i in {1..60}; do
  code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || true)
  [ "$code" = "200" ] && break
  sleep 1
done
[ "$code" = "200" ] || { docker-compose logs --tail=200 api; exit 1; }

ok=$(curl -s http://localhost:8000/openapi.json | jq -r 'has("paths") and (.paths|has("/api/process"))')
[ "$ok" = "true" ] || { echo "/api/process missing"; curl -s http://localhost:8000/openapi.json | jq '.paths|keys'; exit 1; }

MID=$(curl -s -H 'X-Api-Key: demo-key' -X POST http://localhost/api/matters | jq -r '.matter.id')
[ -n "$MID" ] && [ "$MID" != "null" ] || { curl -sS -D - -H 'X-Api-Key: demo-key' -X POST http://localhost/api/matters -o -; exit 1; }

REF=$(curl -s -H 'X-Api-Key: demo-key' http://localhost/api/matters/$MID | jq -r '.matter.ref')
[ -n "$REF" ] && [ "$REF" != "null" ] || { curl -sS -D - -H 'X-Api-Key: demo-key' http://localhost/api/matters/$MID -o -; exit 1; }

OUT=$(curl -s -H 'X-Api-Key: demo-key' -X POST http://localhost/api/process \
  -F "ref=$REF" \
  -F 'llc1_text=Conservation Area. Listed Building. S106 applies.' \
  -F 'con29_text=Enforcement notice: yes. Abutting highway adopted: no. Flood Zone 3. CIL outstanding. Radon affected. Building Regs completion: missing.')
echo "$OUT"

JID=$(echo "$OUT" | jq -r .job_id)
[ -n "$JID" ] && [ "$JID" != "null" ] || { echo "no job_id"; exit 1; }

for i in {1..60}; do
  st=$(curl -s -H 'X-Api-Key: demo-key' http://localhost/jobs/$JID/status | jq -r .status)
  [ "$st" = "finished" ] && break
  sleep 1
done

curl -s -H 'X-Api-Key: demo-key' http://localhost/api/matters/$MID | jq
