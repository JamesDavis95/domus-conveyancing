import os
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from db import SessionLocal, Base, engine
from la.models import LAMatter, LAFinding, LARisk
from la.parsers import parse_llc1, parse_con29
from la.services import parse_and_store, generate_client_report

# Models will be created at startup via main.py lifespan event
# Ensure LA models are imported (done via la.models import)

router = APIRouter(prefix="/la", tags=["Local Authority"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/matters")
def create_matter(ref: str, address: Optional[str] = None, uprn: Optional[str] = None, db: Session = Depends(get_db)):
    m = LAMatter(ref=ref, address=address, uprn=uprn)
    db.add(m); db.commit(); db.refresh(m)
    return {"id": m.id, "ref": m.ref, "address": m.address, "uprn": m.uprn}

@router.post("/matters/{matter_id}/ingest")
async def ingest(matter_id: str, llc1: UploadFile = File(None), con29: UploadFile = File(None), db: Session = Depends(get_db)):
    m = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
    if not m:
        raise HTTPException(404, "Matter not found")
    docs = []
    if llc1 is not None:
        docs.append(("LLC1", await llc1.read()))
    if con29 is not None:
        docs.append(("CON29", await con29.read()))
    if not docs:
        raise HTTPException(400, "Upload at least one of: llc1, con29")
    parse_and_store(db, m, docs)
    return {"status": "INGESTED"}

@router.get("/matters/{matter_id}/risks")
def risks(matter_id: str, db: Session = Depends(get_db)):
    rs = db.query(LARisk).filter(LARisk.matter_id == matter_id).all()
    return [{"code": r.code, "severity": r.severity, "message": r.message} for r in rs]

@router.get("/matters/{matter_id}/report.docx")
def report(matter_id: str, db: Session = Depends(get_db)):
    m = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
    if not m:
        raise HTTPException(404, "Matter not found")
    findings = db.query(LAFinding).filter(LAFinding.matter_id == matter_id).all()
    risks = db.query(LARisk).filter(LARisk.matter_id == matter_id).all()
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"report_{m.ref}.docx")
    generate_client_report(m, findings, risks, out_path)
    return FileResponse(out_path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        filename=os.path.basename(out_path))

@router.get("/matters/{matter_id}/findings")
def findings(matter_id: str, db: Session = Depends(get_db)):
    fs = db.query(LAFinding).filter(LAFinding.matter_id == matter_id).all()
    return [{"key": f.key, "value": f.value, "confidence": f.confidence} for f in fs]

@router.post("/matters/{matter_id}/mock")
def mock_seed(matter_id: str, db: Session = Depends(get_db)):
    m = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
    if not m:
        raise HTTPException(404, "Matter not found")
    llc1 = b"LLC1 SAMPLE\nConservation Area: YES (CA-2015-0032)\n"
    con29 = b"CON29 SAMPLE\nAbutting Highway Adopted: NO\nHighways Authority: HCC Highways\n"
    parse_and_store(db, m, [("LLC1", llc1), ("CON29", con29)])
    return {"status": "SEEDED"}

@router.post("/matters/{matter_id}/reset")
def reset_matter(matter_id: str, db: Session = Depends(get_db)):
    m = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
    if not m:
        raise HTTPException(404, "Matter not found")
    from la.models import LAFinding, LARisk
    db.query(LAFinding).filter(LAFinding.matter_id == matter_id).delete()
    db.query(LARisk).filter(LARisk.matter_id == matter_id).delete()
    db.commit()
    return {"status": "RESET", "matter_id": matter_id}

@router.get("/matters/{matter_id}/export.json")
def export_json(matter_id: str, db: Session = Depends(get_db)):
    m = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
    if not m:
        raise HTTPException(404, "Matter not found")
    fs = db.query(LAFinding).filter(LAFinding.matter_id == matter_id).all()
    rs = db.query(LARisk).filter(LARisk.matter_id == matter_id).all()
    return {
        "matter": {"id": m.id, "ref": m.ref, "address": m.address, "uprn": m.uprn},
        "findings": [{"key": f.key, "value": f.value, "confidence": f.confidence} for f in fs],
        "risks": [{"code": r.code, "severity": r.severity, "message": r.message} for r in rs],
    }
@router.get("/matters/latest")
def latest_matter(db: Session = Depends(get_db)):
    m = db.query(LAMatter).order_by(LAMatter.created_at.desc()).first()
    if not m:
        raise HTTPException(404, "No matters")
    return {"id": m.id, "ref": m.ref, "address": m.address, "uprn": m.uprn}
@router.get("/matters/latest")
def latest_matter(db: Session = Depends(get_db)):
    m = db.query(LAMatter).order_by(LAMatter.created_at.desc()).first()
    if not m:
        raise HTTPException(404, "No matters")
    return {"id": m.id, "ref": m.ref, "address": m.address, "uprn": m.uprn}

@router.get("/matters/latest")
def latest_matter(db: Session = Depends(get_db)):
    m = db.query(LAMatter).order_by(LAMatter.created_at.desc()).first()
    if not m:
        raise HTTPException(404, "No matters")
    return {"id": m.id, "ref": m.ref, "address": m.address, "uprn": m.uprn}
