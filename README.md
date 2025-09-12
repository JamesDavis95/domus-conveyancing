## Auth toggle (optional)
```bash
export AUTH_ENABLED=true
export EXPECTED_API_KEY="demo-key"
# Include this header on API calls:
#   -H "X-Api-Key: demo-key"
```

## Risk scan variants
- **Strict (PDF only)**: `POST /api/matters/{id}/risk-scan` (multipart field `file`). Returns 400 for JSON or non-PDF.
- **UI mode (doc id)**: `POST /api/matters/{id}/risk-scan-json` with `{"doc_id": <int>}`.

## Health endpoints
- `/health` — basic
- `/ready` — DB ping (503 if DB down)
- `/health/av` — whether AV is enabled via env
- `/health/storage` — storage mode + local write test
## OIDC (optional)
Export the following and visit `/login`:
```bash
export OIDC_ENABLED=true
export OIDC_ISSUER="https://login.microsoftonline.com/<tenant-id>/v2.0"
export OIDC_CLIENT_ID="<app-id>"
export OIDC_CLIENT_SECRET="<secret>"
export OIDC_REDIRECT_URI="https://your-host/auth/callback"
export SECRET_KEY="change-me"
```
## SLA & Metrics
`GET /la/metrics/summary` returns:
```json
{ "totals": {"matters": 12, "approved": 7}, "sla": {"avg_seconds_received_to_approved": 86400, "p50_seconds": 72000, "p90_seconds": 129600} }
```

## Jobs (Redis/RQ) — optional
```bash
export REDIS_URL=redis://localhost:6379/0
python worker.py
# UI: use "Async OCR" checkbox; upload enqueues OCR and /api/jobs/{id}/status is polled
```
