from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_process_inline():
    r = client.post("/la/matters/ingest")
    assert r.status_code == 200
    ref = client.get("/la/matters/list").json()["matters"][0]["ref"]
    out = client.post("/api/process", data={
        "ref": ref,
        "llc1_text": "Conservation Area. Listed Building.",
        "con29_text": "Enforcement notice: yes. Abutting highway adopted: no. Flood Zone 3."
    })
    assert out.status_code in (200, 422)
