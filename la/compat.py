from typing import List, Tuple, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Request, Query
from sqlalchemy.orm import Session
from db import SessionLocal
from la.models import LAMatter, LARisk
from la.services import parse_and_store

router = APIRouter(prefix="/api", tags=["Legacy API (compat)"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/list")
def list_matters(db: Session = Depends(get_db)):
    rows = db.query(LAMatter).order_by(LAMatter.created_at.desc()).all()
    return [{"id": m.id, "ref": m.ref, "address": m.address, "uprn": m.uprn} for m in rows]

@router.post("/process")
async def process(
    request: Request,
    ref: Optional[str] = Form(None),
    llc1: UploadFile = File(None),
    con29: UploadFile = File(None),
    # optional fallbacks:
    llc1_text: Optional[str] = Form(None),
    con29_text: Optional[str] = Form(None),
    mock: Optional[bool] = Query(False),
    db: Session = Depends(get_db),
):
    """
    Accepts uploads from legacy UI in many shapes:
    - Files named llc1 / con29 (preferred)
    - Files under unknown keys (file, upload, document, etc.)
    - Text fallbacks: llc1_text / con29_text
    - ?mock=1 to seed without files
    """
    # 1) choose a matter by ref or most recent
    if ref:
        matter = db.query(LAMatter).filter(LAMatter.ref == ref).first()
        if not matter:
            matter = LAMatter(ref=ref)
            db.add(matter); db.commit(); db.refresh(matter)
    else:
        matter = db.query(LAMatter).order_by(LAMatter.created_at.desc()).first()
        if not matter:
            matter = LAMatter(ref="AUTO-1")
            db.add(matter); db.commit(); db.refresh(matter)

    # 2) collect documents from any form field
    docs: List[Tuple[str, bytes]] = []

    # preferred named params
    if llc1 is not None:
        docs.append(("LLC1", await llc1.read()))
    if con29 is not None:
        docs.append(("CON29", await con29.read()))

    # any other file fields via raw form
    try:
        form = await request.form()
        for key, value in form.multi_items():
            # UploadFile instances
            if hasattr(value, "read") and hasattr(value, "filename"):
                content = await value.read()
                kind = "LLC1" if "llc1" in key.lower() else ("CON29" if "con29" in key.lower() else "CON29")
                docs.append((kind, content))
    except Exception:
        pass

    # text fallbacks
    if llc1_text:
        docs.append(("LLC1", llc1_text.encode("utf-8")))
    if con29_text:
        docs.append(("CON29", con29_text.encode("utf-8")))

    # mock seed
    if mock and not docs:
        llc1_mock = b"LLC1 SAMPLE\nConservation Area: YES (CA-2015-0032)\n"
        con29_mock = b"CON29 SAMPLE\nAbutting Highway Adopted: NO\nHighways Authority: HCC Highways\nPlanning Permission: 3/19/1234/FUL Granted 2019-06-12 Rear extension\n"
        docs = [("LLC1", llc1_mock), ("CON29", con29_mock)]

    if not docs:
        raise HTTPException(400, "No documents received. Send files (llc1/con29), llc1_text/con29_text, or use ?mock=1")

    # 3) parse -> findings -> risks
    parse_and_store(db, matter, docs)

    risks = db.query(LARisk).filter(LARisk.matter_id == matter.id).all()
    return {
        "matter_id": matter.id,
        "ref": matter.ref,
        "risks": [{"code": r.code, "severity": r.severity, "message": r.message} for r in risks],
    }
