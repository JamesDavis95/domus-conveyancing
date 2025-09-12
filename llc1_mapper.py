from typing import Iterable, Dict
from models import Findingss, Risk  # types only

_CANON = {
    "CONSERVATION_AREA": ["LLC1_CONSERVATION","CONSERVATION_AREA"],
    "LISTED_BUILDING": ["LLC1_LISTED","LISTED_BUILDING"],
    "TREE_PRESERVATION_ORDER": ["LLC1_TPO","TREE_PRESERVATION_ORDER"],
    "ARTICLE_4_DIRECTION": ["LLC1_ARTICLE4","ARTICLE_4_DIRECTION"],
    "ENFORCEMENT_NOTICE": ["LLC1_ENFORCEMENT","ENFORCEMENT_NOTICE"],
    "FINANCIAL_CHARGES": ["LLC1_FINANCIAL_CHARGE","CIL_OR_S106","SECTION_106","CIL"],
    "SMOKE_CONTROL": ["LLC1_SMOKE_CONTROL","SMOKE_CONTROL"],
    "LIGHTING_CONSENT": ["LLC1_LIGHTING","LIGHTING_CONSENT"],
}

def _yes(v: str) -> str:
    if not v: return "Yes"
    v = v.strip()
    return f"Yes — {v}" if v else "Yes"

def map_llc1(findings: Iterable[Finding], risks: Iterable[Risk]) -> Dict[str,str]:
    """
    Very simple normalisation:
      - If a matching finding exists → 'Yes' (+ value)
      - Else if a matching risk exists → 'Yes'
      - Else → 'No information held' (not authoritative)
    """
    f_by_type = {}
    for f in findings or []:
        t = (f.type or "").upper().strip()
        if t and t not in f_by_type:
            f_by_type[t] = f

    r_codes = set((r.code or "").upper().strip() for r in (risks or []) if (r.code or "").strip())

    out = {}
    for key, aliases in _CANON.items():
        has_f = next((f_by_type[a] for a in aliases if a in f_by_type), None)
        has_r = any(a in r_codes for a in aliases)
        if has_f:
            out[key] = _yes(has_f.value or "")
        elif has_r:
            out[key] = "Yes"
        else:
            out[key] = "No information held"
    return out
