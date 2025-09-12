You are fixing this FastAPI service end-to-end.

Goals:
1) Ensure DB uses Postgres via env DATABASE_URL; add safe default in db.py (no _os alias); create tables on first run.
2) /api/matters -> ingest via /la/matters/ingest and return the last matter (id+ref). Make robust.
3) /la/matters/export.json and /la/matters/report.docx -> call build_json(mid, [], []) and build_docx(mid, [], []); never require risks/findings from caller.
4) /api/matters/{id}/risk-scan must accept multipart PDF (field "file"); if JSON is sent, return clear 400 "PDF required".
5) Stop /jobs//status 404 spam (remove or guard).
6) Harden /health and /metrics; if PROMETHEUS_MULTIPROC_DIR missing, fall back to single-process collector.
Please:
- Search the repo and make all code changes to achieve these goals.
- Add minimal logging on errors (status code + message).
- Don’t change public response shapes existing curl examples rely on.
- Add a README Quickstart with curl smoke tests for these endpoints.
- Commit logically with clear messages.
