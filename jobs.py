from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select
from db import SessionLocal, Matters, Findings, Risks
from la.parsers import parse_llc1, parse_con29
from la.schemas import LLC1, Con29

def _set_status(mid: int, status: str):
    with SessionLocal() as s:
        m = s.get(Matters, mid)
        if m:
            m.status = status
            s.commit()

def _ins_findings(mid: int, items: List[Tuple[str,str,Optional[dict]]]):
    with SessionLocal() as s:
        for kind, value, ev in items:
            s.add(Findings(matter_id=mid, kind=kind, value=value, evidence_json=(None if ev is None else __import__("json").dumps(ev))))
        s.commit()

def _ins_risks(mid: int, items: List[Tuple[str,str,Optional[dict]]]):
    with SessionLocal() as s:
        for code, level, ev in items:
            s.add(Risks(matter_id=mid, code=code, level=level, evidence_json=(None if ev is None else __import__("json").dumps(ev))))
        s.commit()

def parse_and_persist(matter_id: int,
                      llc1_text: Optional[str],
                      con29_text: Optional[str],
                      llc1_key: Optional[str],
                      con29_key: Optional[str]) -> Dict[str, Any]:
    _set_status(matter_id, "processing")
    llc1_obj: Optional[LLC1] = parse_llc1(llc1_text or "") if llc1_text else None
    con29_obj: Optional[Con29] = parse_con29(con29_text or "") if con29_text else None

    findings: List[Tuple[str,str,Optional[dict]]] = []
    risks:    List[Tuple[str,str,Optional[dict]]] = []

    # Findings with evidence JSON
    if llc1_obj:
        for c in llc1_obj.charges:
            findings.append(("LLC1:Charge", f"{c.charge_type}={c.present}", {"file_key": llc1_key, "page": c.evidence.page if c.evidence else None}))
    if con29_obj:
        findings += [
            ("CON29:Enforcement", str(con29_obj.enforcement_notices_present), {"file_key": con29_key}),
            ("CON29:ContaminatedLand", str(con29_obj.contaminated_land_designation), {"file_key": con29_key}),
            ("CON29:S106", str(con29_obj.s106_present), {"file_key": con29_key}),
            ("CON29:CIL", str(con29_obj.cil_outstanding), {"file_key": con29_key}),
            ("CON29:FloodZone", str(con29_obj.flood_zone), {"file_key": con29_key}),
            ("CON29:Radon", str(con29_obj.radon_affected), {"file_key": con29_key}),
            ("CON29:BuildingRegsCompletion", str(con29_obj.building_regs_completion_present), {"file_key": con29_key}),
        ]
    _ins_findings(matter_id, findings)

    # Simple risk engine w/ evidence link
    if con29_obj and con29_obj.roads_footways and con29_obj.roads_footways.abutting_highway_adopted is False:
        risks.append(("UnadoptedRoad", "HIGH", {"file_key": con29_key}))
    if llc1_obj and any(c.charge_type.lower().startswith("conservation") and c.present for c in llc1_obj.charges):
        risks.append(("ConservationArea", "MEDIUM", {"file_key": llc1_key}))
    if llc1_obj and any(c.charge_type.lower().startswith("listed") and c.present for c in llc1_obj.charges):
        risks.append(("ListedBuilding", "MEDIUM", {"file_key": llc1_key}))
    if con29_obj and con29_obj.enforcement_notices_present:
        risks.append(("EnforcementNotice", "MEDIUM", {"file_key": con29_key}))
    if con29_obj and con29_obj.cil_outstanding:
        risks.append(("CILOutstanding", "MEDIUM", {"file_key": con29_key}))
    if con29_obj and (con29_obj.flood_zone == "3"):
        risks.append(("FloodZone3", "HIGH", {"file_key": con29_key}))
    if con29_obj and con29_obj.radon_affected:
        risks.append(("RadonAffected", "MEDIUM", {"file_key": con29_key}))
    if con29_obj and (con29_obj.building_regs_completion_present is False):
        risks.append(("MissingBuildingRegs", "MEDIUM", {"file_key": con29_key}))

    _ins_risks(matter_id, risks)
    _set_status(matter_id, "done")
    return {"matter_id": matter_id, "findings": len(findings), "risks": len(risks)}
