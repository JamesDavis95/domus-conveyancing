from fastapi.testclient import TestClient
from app_secured import app

def test_docx_download(tmp_path):
    c = TestClient(app)
    r = c.post("/api/matters", json={})
    mid = r.json()["matter"]["id"]
    # Should return a docx even without risks/findings
    docx = c.get(f"/la/matters/{mid}/report.docx")
    assert docx.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in docx.headers.get("content-type","")
