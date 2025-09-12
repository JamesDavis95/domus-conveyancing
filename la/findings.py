from fastapi import APIRouter, HTTPException
from models import SessionLocal, Findings

router = APIRouter()

@router.get("/la/matters/{mid}/findings")
def get_findings(mid: int):
    with SessionLocal() as session:
        findings = session.query(Findings).filter(Findings.matter_id == mid).all()
        if not findings:
            raise HTTPException(404, "No findings for this matter")
        return {"findings": [{"key": f.key, "value": f.value, "confidence": f.confidence} for f in findings]}