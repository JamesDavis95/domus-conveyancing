import io, time
from fastapi.testclient import TestClient
from app_secured import app

c = TestClient(app)

def _mk_pdf():
    return b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n"

def test_upload_rejects_non_pdf(monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_MB","1")
    r = c.post("/api/matters", json={"council":"Test"})
    mid = r.json()["matter"]["id"]
    files = {"file": ("x.txt", io.BytesIO(b"hello"), "text/plain")}
    r2 = c.post(f"/api/matters/{mid}/upload?kind=search", files=files)
    assert r2.status_code == 400

def test_publish_and_public_links():
    # create + upload
    r = c.post("/api/matters", json={"council":"Test"})
    mid = r.json()["matter"]["id"]
    files = {"file": ("ok.pdf", io.BytesIO(_mk_pdf()), "application/pdf")}
    assert c.post(f"/api/matters/{mid}/upload?kind=search", files=files).status_code == 200
    # approve, publish
    assert c.post(f"/la/matters/{mid}/approve").status_code == 200
    pub = c.post(f"/la/matters/{mid}/publish").json()
    assert pub["ok"] is True
    links = pub["links"]
    # passport
    pr = c.get(links["passport"])
    assert pr.status_code == 200
    # export json
    jr = c.get(links["export_json"])
    assert jr.status_code == 200
    # llc1 docx
    lr = c.get(links["llc1_docx"])
    assert lr.status_code == 200
