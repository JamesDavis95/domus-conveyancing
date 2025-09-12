import os, tempfile, subprocess
from parsers.pdf_text import extract_pdf_text
from db import SessionLocal
from models import Matters, File as FileModel, Finding, Risk as RiskModel
from risk_engine import run as run_rules
from datetime import datetime, timezone

def ocr_text_task(path: str) -> dict:
    text = extract_pdf_text(path) or ""
    if len((text or "").strip()) >= 100:
        return {"applied": False, "text": text}
    if os.getenv("OCR_ENABLED","true").lower() != "true":
        return {"applied": False, "text": text}
    try:
        out = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
        subprocess.run(["ocrmypdf","--quiet","--force-ocr", path, out], check=True)
        text2 = extract_pdf_text(out) or text
        return {"applied": True, "text": text2}
    except Exception:
        return {"applied": False, "text": text}

def process_scan_task(matter_id: int, doc_id: int) -> dict:
    """Full pipeline in background: OCR-if-needed → rules → persist."""
    db = SessionLocal()
    try:
        m = db.get(Matter, matter_id)
        d = db.get(FileModel, doc_id)
        if not m or not d: return {"ok": False, "error": "not found"}
        text = extract_pdf_text(d.path or "") or ""
        applied = False
        if len((text or "").strip()) < 100 and os.getenv("OCR_ENABLED","true").lower() == "true":
            res = ocr_text_task(d.path or "")
            applied = bool(res.get("applied"))
            text = res.get("text") or text
            if applied and not d.ocr_applied:
                d.ocr_applied = True
                db.commit()
        result = run_rules(text)
        # persist
        for f in result.get("findings", []):
            db.add(Finding(matter_id=m.id, type=f.get("type","GENERIC"), value=f.get("value",""), source_ref=f.get("source_ref")))
        created = 0
        for r in result.get("risks", []):
            db.add(RiskModel(matter_id=m.id, code=r["code"], severity=r.get("severity","medium"), explanation=r.get("explanation",""), evidence_ref=str(d.id)))
            created += 1
        if not m.first_scan_at:
            m.first_scan_at = datetime.now(timezone.utc)
            if m.status == "draft":
                m.status = "review"
        db.commit()
        return {"ok": True, "applied_ocr": applied, "risks_created": created}
    finally:
        db.close()
