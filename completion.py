from typing import Dict, Any

def sdlt_draft(rec: Dict[str,Any]) -> Dict[str,Any]:
    ex = rec.get("extracted_json") or {}
    addr = ex.get("property_address") or ""
    # Minimal fields for demo; expand as needed
    return {
        "form": "SDLT-DRAFT",
        "property_address": addr,
        "purchaser": "TBC",
        "consideration": "TBC",
        "is_lease": "Yes" if "lease" in (addr.lower()) else "No",
        "notes": "Auto-prepared skeleton—conveyancer to confirm before submission."
    }
