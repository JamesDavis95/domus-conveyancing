import re
from typing import Dict

def parse_conveyancing(text: str) -> Dict:
    """Extract key conveyancing fields from local search text."""
    def has(pattern: str) -> bool:
        return bool(re.search(pattern, text, re.IGNORECASE))

    def grab(pattern: str) -> str:
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1).strip() if m else ""

    return {
        "conservation_area": has(r"Conservation Area\s*[:\-]?\s*(Yes|Present|Applies)"),
        "listed_building": {
            "present": has(r"Listed Building"),
            "grade": grab(r"Listed Building.*?(Grade\s*[IIV]+)")
        },
        "tpo": re.findall(r"(?:TPO|Tree Preservation Order).*?(?:No\.?|Ref).*?([A-Z0-9/]+)", text, re.IGNORECASE),
        "road_status": grab(r"(Adopted highway|Unadopted road|Highway maintainable at public expense)"),
        "planning_refs": re.findall(r"\b\d{1,2}/\d{2,4}/\d{1,5}/[A-Z]{2,4}\b", text),
        "enforcement_notices": has(r"Enforcement Notice.*?(Yes|Served|Applies)"),
        "contaminated_land": has(r"Contaminated Land|Part IIA"),
        "radon_band": grab(r"Radon.*?:\s*([^\n]+)"),
        "flood_zone": grab(r"Flood Zone.*?:\s*([^\n]+)")
    }
