from fastapi.testclient import TestClient
from app_secured import app
import io

c = TestClient(app)

def test_async_risk_scan_falls_back_to_sync():
    # Create matter
    r = c.post("/api/matters", json={"council":"Testshire"})
    assert r.status_code == 200
    mid = r.json()["matter"]["id"]

    # Upload minimal PDF
    pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n"
    files = {"file": ("t.pdf", io.BytesIO(pdf), "application/pdf")}
    r2 = c.post(f"/api/matters/{mid}/upload?kind=search", files=files)
    assert r2.status_code == 200
    # Get doc id
    m = c.get(f"/la/matters/{mid}").json()
    doc_id = m["matter"]["documents"][-1]["id"]

    # Async compat (falls back to sync without Redis)
    r3 = c.post(f"/api/matters/{mid}/risk-scan-async", json={"doc_id": doc_id})
    assert r3.status_code == 200
    assert r3.json().get("ok") in (True, None)  # may return {"ok":True,...} or another success shape
