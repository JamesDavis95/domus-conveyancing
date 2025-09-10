import re
from typing import Dict, Any

def parse_title_text(text: str) -> Dict[str, Any]:
    # Toy parser—extract some useful bits we’ll expand later
    out: Dict[str, Any] = {"plain_english": []}
    if not text:
        return out
    # Restrictions
    restr = re.findall(r"Restriction:\s*(.+)", text, re.I)
    if restr:
        out["restrictions"] = [r.strip() for r in restr][:10]
        out["plain_english"].append(f"{len(out['restrictions'])} restriction(s) found.")
    # Easements
    eas = re.findall(r"easement[s]?:\s*(.+)", text, re.I)
    if eas:
        out["easements"] = [e.strip() for e in eas][:10]
        out["plain_english"].append(f"Easements mentioned.")
    # Charges
    chg = re.findall(r"charge[s]?:\s*(.+)", text, re.I)
    if chg:
        out["charges"] = [c.strip() for c in chg][:10]
        out["plain_english"].append("Registered charge(s) present.")
    # Lease length hint
    m = re.search(r"\bterm\s+of\s+(\d{2,3})\s+years\b", text, re.I)
    if m:
        out["lease_years"] = int(m.group(1))
        out["plain_english"].append(f"Lease length ~{out['lease_years']} years.")
    return out

def summarise_title(title: Dict[str, Any]) -> Dict[str, Any]:
    issues = []
    if title.get("lease_years") and title["lease_years"] < 80:
        issues.append(f"Short lease (~{title['lease_years']}y): lender may require extension.")
    if title.get("restrictions"):
        issues.append("Title restrictions present—review wording and consents.")
    if title.get("charges"):
        issues.append("Registered charge(s) present—lender interactions likely.")
    return {"summary": "; ".join(issues) or "No critical issues detected.", "issues": issues}
