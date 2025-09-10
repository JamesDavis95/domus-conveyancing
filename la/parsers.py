import re
from typing import List, Optional
from .schemas import Con29, LLC1, PlanningDecision, RoadsFootways, Charge

_re_true = re.compile(r"\b(yes|present|true|y|provided|outstanding|payable|affected)\b", re.I)
_re_false = re.compile(r"\b(no|absent|false|n|none|not\s*affected|missing)\b", re.I)

def _parse_bool(fragment: Optional[str]) -> Optional[bool]:
    if fragment is None:
        return None
    if _re_true.search(fragment):
        return True
    if _re_false.search(fragment):
        return False
    return None

def parse_llc1(text: str) -> LLC1:
    charges: List[Charge] = []

    def add(charge_type: str, pattern: str):
        present = bool(re.search(pattern, text or "", re.I|re.S))
        charges.append(Charge(charge_type=charge_type, present=present, source="LLC1"))

    add("ConservationArea", r"\bconservation\s+area\b")
    add("ListedBuilding", r"\blisted\s+building\b")
    add("TPO", r"\b(tree\s+preservation|TPO)\b")
    add("S106", r"\b(section\s*106|s106)\b")
    return LLC1(charges=charges)

def parse_con29(text: str) -> Con29:
    text = text or ""

    decisions: List[PlanningDecision] = []
    for ref, desc, decision, date in re.findall(
        r"(?:ref(?:erence)?[:\s]*([A-Z0-9/\-]+))?.{0,80}?"
        r"(?:desc(?:ription)?[:\s]*(.{0,160}?))?.{0,60}?"
        r"(?:decision[:\s]*(granted|refused|approved|undetermined))?.{0,60}?"
        r"(?:date[:\s]*([0-9]{1,2}\s\w+\s[0-9]{2,4}|[0-9\/\-]{6,10}))?",
        text, re.I|re.S):
        if any([ref, desc, decision, date]):
            decisions.append(PlanningDecision(
                ref=(ref or "N/A").strip(),
                description=(desc or None).strip() if desc else None,
                decision=(decision or None),
                date=(date or None),
                evidence=None
            ))

    m_adopt = re.search(r"(?:abutting.*?adopted|highway.*adopted).*?(yes|no|true|false)", text, re.I|re.S)
    highways = RoadsFootways(
        abutting_highway_adopted=_parse_bool(m_adopt.group(1) if m_adopt else None),
        authority=None,
        evidence=None
    )

    m_enf = re.search(r"\benforcement\s+notice(?:s)?\b.*?(yes|no|true|false)", text, re.I|re.S)
    enf = _parse_bool(m_enf.group(1) if m_enf else None)
    m_contam = re.search(r"\bcontaminated\s+land\b.*?(yes|no|true|false)", text, re.I|re.S)
    contam = _parse_bool(m_contam.group(1) if m_contam else None)

    m_s106 = re.search(r"\b(section\s*106|s106)\b.*?(yes|no|true|false|outstanding|payable|none)", text, re.I|re.S)
    s106 = _parse_bool(m_s106.group(2) if m_s106 else None)

    m_cil = re.search(r"\bCIL\b.*?(yes|no|true|false|outstanding|none|payable)", text, re.I|re.S)
    cil_out = _parse_bool(m_cil.group(1) if m_cil else None)

    flood_zone = None
    m_fz = re.search(r"\bflood\s*zone\s*(1|2|3)\b", text, re.I)
    if m_fz:
        flood_zone = m_fz.group(1)

    m_rad = re.search(r"\bradon\b.*?(affected|not\s*affected|yes|no|true|false)", text, re.I|re.S)
    radon = _parse_bool(m_rad.group(1) if m_rad else None)

    m_br = re.search(r"\b(building\s*reg(ulation)?s?|completion\s*certificate)\b.*?(provided|missing|yes|no|true|false)", text, re.I|re.S)
    br_comp = _parse_bool(m_br.group(3) if m_br else None)

    return Con29(
        planning_decisions=decisions,
        roads_footways=highways,
        enforcement_notices_present=enf,
        contaminated_land_designation=contam,
        s106_present=s106,
        cil_outstanding=cil_out,
        flood_zone=flood_zone,
        radon_affected=radon,
        building_regs_completion_present=br_comp
    )
