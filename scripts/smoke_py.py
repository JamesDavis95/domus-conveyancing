import os, time, sys, requests, json
BASE = os.getenv("BASE", "http://localhost:8000")

def main():
    # health
    r = requests.get(f"{BASE}/health", timeout=5); r.raise_for_status()
    # ingest
    m = requests.post(f"{BASE}/la/matters/ingest", timeout=10); m.raise_for_status()
    ref = m.json()["matter"]["ref"]
    # process
    p = requests.post(f"{BASE}/api/process", data={"ref":ref,"llc1_text":"Conservation Area.","con29_text":"Abutting highway adopted: no."}, timeout=20)
    p.raise_for_status()
    js = p.json()
    jid = js.get("job_id")
    if jid:
        t0=time.time()
        while time.time()-t0<30:
            s = requests.get(f"{BASE}/jobs/{jid}/status", timeout=5); s.raise_for_status()
            if s.json().get("status")=="finished": break
            time.sleep(0.5)
    # verify detail has at least one risk
    lst = requests.get(f"{BASE}/la/matters/list", timeout=5); lst.raise_for_status()
    mid = lst.json()["matters"][0]["id"]
    det = requests.get(f"{BASE}/la/matters/{mid}/detail", timeout=5); det.raise_for_status()
    risks = det.json().get("risks", [])
    assert len(risks)>=1, "Expected >=1 risks"
    print("SMOKE OK")
if __name__=="__main__":
    main()
