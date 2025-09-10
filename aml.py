import time, hashlib, csv, io
from typing import Dict, Any, List

# ---- KYC MOCK ----
# We simulate a KYC provider workflow you can swap for Onfido/Veriff later.
_STATE: Dict[str, Dict[str, Any]] = {}

def aml_start(client_name: str, email: str) -> Dict[str, Any]:
    token = hashlib.sha1(f"{client_name}|{email}|{time.time()}".encode()).hexdigest()[:16]
    _STATE[token] = {"client": client_name, "email": email, "status": "pending"}
    return {"token": token, "provider_url": f"https://kyc.example/{token}", "status": "pending"}

def aml_status(token: str) -> Dict[str, Any]:
    rec = _STATE.get(token) or {}
    # simulate auto-approval after ~15s window
    if rec and rec.get("status") == "pending" and time.time() % 17 < 8:
        rec["status"] = "approved"
    return {"token": token, "status": rec.get("status", "unknown")}

# ---- PROOF OF FUNDS (BANK CSV) ----
# Accepts a simple CSV with headers: date, description, amount, balance
# Flags: single-source deposit size, unusual inflows, cash deposits.
def parse_bank_csv(file_bytes: bytes) -> Dict[str, Any]:
    text = file_bytes.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))
    inflows: List[float] = []
    cash_deposits = 0
    largest = 0.0
    total_in = 0.0
    rows = []
    for r in reader:
        try:
            amt = float(r.get("amount","0").replace(",",""))
        except:
            amt = 0.0
        desc = (r.get("description","") or "").lower()
        if amt > 0:
            inflows.append(amt)
            total_in += amt
            if amt > largest: largest = amt
            if "cash" in desc or "atm" in desc:
                cash_deposits += 1
        rows.append(r)
    flags = []
    if largest >= max(10000, 0.5*total_in) and total_in > 0:
        flags.append("Large single-source inflow; obtain evidence of origin.")
    if cash_deposits >= 1:
        flags.append("Cash deposits present; may require enhanced due diligence.")
    return {
        "summary": {
            "total_in": round(total_in,2),
            "largest_inflow": round(largest,2),
            "cash_deposits_count": cash_deposits,
            "num_rows": len(rows),
        },
        "flags": flags
    }
