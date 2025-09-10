import io, re
from typing import Dict, Any, List
from PyPDF2 import PdfReader

# OCR fallback
try:
    import pytesseract
    from pdf2image import convert_from_bytes
    _OCR_OK = True
except Exception:
    _OCR_OK = False

def pdf_to_text(file_bytes: bytes) -> str:
    """Extract text via PyPDF2; if very short and OCR available, use OCR fallback."""
    # Try native
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        buf = []
        for i, page in enumerate(reader.pages):
            buf.append(page.extract_text() or "")
        text = "\n\n".join(buf).strip()
        if len(text) >= 400 or not _OCR_OK:
            return text
    except Exception:
        # fall through to OCR if available
        pass

    if not _OCR_OK:
        return ""

    # OCR fallback
    try:
        images = convert_from_bytes(file_bytes, dpi=300)  # needs poppler installed
        parts = []
        for idx, img in enumerate(images):
            parts.append(pytesseract.image_to_string(img))
        return "\n\n".join(parts).strip()
    except Exception:
        return ""

def _grab(pattern: str, text: str, flags=re.I | re.M) -> str:
    if not isinstance(text, (str, bytes)):
        return ""
    m = re.search(pattern, text, flags)
    return (m.group(1).strip() if m else "")

def _find_all(pattern: str, text: str, flags=re.I | re.M) -> List[str]:
    if not isinstance(text, (str, bytes)):
        return []
    return [m.strip() for m in re.findall(pattern, text, flags)]

def extract_with_ocr_fallback(file_bytes: bytes) -> Dict[str, Any]:
    raw = pdf_to_text(file_bytes)
    return conv_extract_from_text(raw)

def conv_extract_from_text(text: str) -> Dict[str, Any]:
    if not isinstance(text, str):
        text = ""

    # Planning refs like 12/3746, 12/3746N, SP/03/12
    refs = list(set(_find_all(r"\b[A-Z]{0,3}\/?\d{2,4}\/?\d{1,4}[A-Z]?\b", text)))

    # Basic flood mentions
    flood_norm = ""
    if re.search(r"\bflood\s*zone\s*3\b", text, re.I): flood_norm = "Flood Zone 3"
    elif re.search(r"\bflood\s*zone\s*2\b", text, re.I): flood_norm = "Flood Zone 2"
    elif re.search(r"surface\s*water", text, re.I): flood_norm = "Surface water (screen)"

    # TPO + S106 + Conservation
    tpo_present = bool(re.search(r"\bTPO\b|\bTree Preservation\b", text, re.I))
    s106_present = bool(re.search(r"\bSection\s*106\b|\bS106\b", text, re.I))
    cil_present = bool(re.search(r"\bCommunity Infrastructure Levy\b|\bCIL\b", text, re.I))
    consv_present = bool(re.search(r"\bConservation Area\b", text, re.I))

    # Council (best effort)
    council_guess = _grab(r"(?:Local\s+Authority|Council|Authority)\s*:\s*([^\n]+)", text)
    # Address (very rough, gets anything that looks like an address heading)
    address_guess = _grab(r"(?:Address|Site\s*Address)\s*:\s*([^\n]+)", text)
    if not address_guess:
        # fallback: first long line that looks like an address
        m = re.search(r"([A-Za-z0-9 ,.-]{15,}?)\s+(?:Tel|Telephone|Email)\b", text, re.I)
        address_guess = (m.group(1).strip() if m else "")

    extracted = {
        "council": (council_guess or "").strip(),
        "property_address": (address_guess or "").strip(),
        "uprn": "",
        "planning_references": refs,
        "flood_zone": flood_norm,
        "contamination": "",
        "restrictions": [],
        "raw_length_chars": len(text),
        # Conveyancing block
        "conveyancing": {
            "llc1": {
                "listed_building": False,
                "listed_building_grade": "",
                "conservation_area": bool(consv_present),
                "conservation_area_name": "",   # can be improved with gazetteer match later
                "tpo": bool(tpo_present),
                "tpo_refs": "",
                "article4": False,
                "article4_refs": "",
                "financial_charges": False,
                "financial_charges_details": "",
                "s106": bool(s106_present),
                "s106_refs": "",   # try to grab line around s106 later
                "cil": bool(cil_present),
                "smoke_control": False,
                "heritage_designations": ""
            },
            "con29": {
                "road_status": None,
                "road_status_confidence": "low",
                "planning_refs": refs,
                "enforcement_notices": False,
                "stop_notices": False,
                "building_regulations": False,
                "traffic_schemes_pending": False,
                "compulsory_purchase": False,
                "pipeline": False,
                "contaminated_land_determination": False,
                "assets_of_community_value": False,
                "radon_band": ""
            },
            "water_drainage": {
                "adopted_sewer_within_boundary": False,
                "public_sewer_within_3m": False,
                "water_main_within_property": False,
                "build_over_agreement": False,
                "surface_water_drainage_connected": False
            },
            "environmental": {
                "flood_zone": flood_norm,
                "historic_landfill_within_250m": False,
                "coal_mining_area": False
            }
        }
    }
    return extracted
