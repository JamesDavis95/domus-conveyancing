import os, time, random, sys
import requests

BASE = os.getenv("BASE", "http://localhost:8000")

SAMPLES = [
  ("Conservation Area. Listed Building. S106 applies.",
   "Enforcement notice: yes. Abutting highway adopted: no. Flood Zone 3. CIL outstanding. Radon affected. Building Regs completion: missing."),
  ("No designations noted.",
   "Enforcement notice: no. Abutting highway adopted: yes. Flood Zone 1. CIL clear. Radon low. Building Regs completion: present."),
  ("Property is in Conservation Area.",
   "Abutting highway adopted: no. Flood Zone 2. CIL maybe. Radon affected.")
]

def jget(r):
    try:
        r.raise_for_status()
        return r.json()
    except Exception:
        sys.stderr.write(f"\nHTTP {r.status_code} {r.url}\n{r.text[:400]}\n")
        raise

def poll(job_id, timeout=30):
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = requests.get(f"{BASE}/jobs/{job_id}/status", timeout=5)
        r.raise_for_status()
        js = r.json()
        if js.get("status") == "finished":
            return True
        time.sleep(0.5)
    return False

def main(n=10):
    # sanity: health
    h = requests.get(f"{BASE}/health", timeout=5)
    h.raise_for_status()
    for _ in range(n):
        # 1) create a matter
        m = jget(requests.post(f"{BASE}/la/matters/ingest", timeout=10))
        ref = m["matter"]["ref"]
        llc1, con29 = random.choice(SAMPLES)
        # 2) process
        r = requests.post(f"{BASE}/api/process", data={"ref": ref, "llc1_text": llc1, "con29_text": con29}, timeout=20)
        js = jget(r)
        jid = js.get("job_id")
        if jid:
            ok = poll(jid, 60)
            if not ok:
                raise RuntimeError(f"Job {jid} did not finish in time")
    print("Seeded.")

if __name__ == "__main__":
    main(int(os.getenv("N","10")))
