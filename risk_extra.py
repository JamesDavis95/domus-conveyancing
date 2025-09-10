import re
from typing import Dict, Any, List

def from_title_blocks(title: Dict[str, Any]) -> Dict[str, Any]:
    risks: List[str] = []
    lease_years = None
    text_join = " ".join(title.get("covenants", []) + title.get("restrictions", []) + title.get("plain_english", []))
    m = re.search(r"lease\s+.*?(\d{2,3})\s*years", text_join, re.I)
    if m:
        try: lease_years = int(m.group(1))
        except: lease_years = None
    if lease_years is not None and lease_years < 80:
        risks.append(f"Short lease: ~{lease_years} years. Lender may not accept without extension.")
    for kw in ["fensa","gas safe","building control","completion certificate"]:
        if not re.search(kw, text_join, re.I):
            pass  # absence isn't proof—leave it for checklist UI
    return {"lease_years": lease_years, "extra_risks": risks}

def checklist_from_extracted(extracted: Dict[str,Any]) -> Dict[str,Any]:
    llc = (extracted.get("conveyancing",{}) or {}).get("llc1",{}) if isinstance(extracted, dict) else {}
    needs = []
    if llc.get("s106"): needs.append("Section 106 agreement—obligations/charges.")
    if llc.get("tpo"): needs.append("Tree Preservation—check works consents.")
    flood = (extracted.get("flood_zone") or (extracted.get("conveyancing",{}).get("environmental",{}) or {}).get("flood_zone") or "")
    if re.search(r"high|zone\s*3", str(flood), re.I): needs.append("Potential flood exposure—insurer/lender may require conditions.")
    return {"checklist": needs}
