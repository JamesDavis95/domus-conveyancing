#!/usr/bin/env bash
set -euo pipefail

curl -s http://localhost:8000/health
curl -s http://localhost:8000/ready

until curl -s http://localhost:8000/ready | grep -q '"ok":true'; do sleep 1; done

curl -s -X POST http://localhost:8000/la/matters/ingest
REF=$(curl -s http://localhost:8000/la/matters/list | jq -r '.matters[0].ref')

OUT=$(curl -s -X POST http://localhost:8000/api/process   -F "ref=$REF"   -F 'llc1_text=Conservation Area. Listed Building. S106 applies.'   -F 'con29_text=Enforcement notice: yes. Abutting highway adopted: no. Flood Zone 3. CIL outstanding. Radon affected. Building Regs completion: missing.')

echo "$OUT"
JID=$(echo "$OUT" | jq -r .job_id)
until [ "$(curl -s http://localhost:8000/jobs/$JID/status | jq -r .status)" = "finished" ]; do sleep 1; done

MID=$(curl -s http://localhost:8000/la/matters/list | jq -r '.matters[0].id')
curl -s "http://localhost:8000/la/matters/$MID/detail" | jq

echo "Report: http://localhost:8000/la/matters/$MID/report.docx"
echo "Export: http://localhost:8000/la/matters/$MID/export.json"
