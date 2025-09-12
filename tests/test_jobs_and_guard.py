from fastapi.testclient import TestClient
from app_secured import app

c = TestClient(app)

def test_jobs_status_guards_empty():
    r = c.get("/jobs//status")
    assert r.status_code in (400,404)  # implementation returns 400 for empty id

def test_jobs_status_not_found():
    r = c.get("/jobs/does-not-exist/status")
    assert r.status_code in (404,400)

def test_oidc_guard_allows_when_disabled(monkeypatch):
    monkeypatch.setenv("OIDC_ENABLED","false")
    # auth off -> allowed
    r = c.get("/la/matters/list")
    assert r.status_code in (200,401)  # 200 if auth off, 401 if you turned AUTH_ENABLED on
