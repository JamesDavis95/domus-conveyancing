from fastapi.testclient import TestClient
from app_secured import app

def test_risk_scan_requires_multipart():
    c = TestClient(app)
    r = c.post("/api/matters", json={})
    mid = r.json()["matter"]["id"]
    # Send JSON -> should 400
    bad = c.post(f"/api/matters/{mid}/risk-scan", json={"doc_id": 123})
    assert bad.status_code == 400

def test_risk_scan_multipart_ok(tmp_path):
    c = TestClient(app)
    r = c.post("/api/matters", json={})
    mid = r.json()["matter"]["id"]
    pdf = tmp_path/"t.pdf"; pdf.write_bytes(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n")
    r2 = c.post(f"/api/matters/{mid}/risk-scan", files={"file": ("t.pdf", pdf.read_bytes(), "application/pdf")})
    assert r2.status_code == 200
