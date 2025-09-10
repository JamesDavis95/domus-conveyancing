from fastapi import APIRouter, Depends, HTTPException, Request, Form

# --- SAFE WRAPPERS (durable) ---
def _call_build_docx(mid, risks=None, findings=None):
    risks = risks or []
    findings = findings or []
    try:
        # prefer keyword args (handles keyword-only signatures)
        return build_docx(mid, risks=risks, findings=findings)
    except TypeError:
        try:
            # some versions accept positional lists
            return build_docx(mid, risks, findings)
        except TypeError:
            # oldest versions only take mid
            return build_docx(mid)

def _call_build_json(mid, risks=None, findings=None):
    risks = risks or []
    findings = findings or []
    try:
        return build_json(mid, risks=risks, findings=findings)
    except TypeError:
        try:
            return build_json(mid, risks, findings)
        except TypeError:
            return build_json(mid)
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy import select, desc
from db import SessionLocal, Matters, Findings, Risks
from settings import settings
from reports import build_docx, build_json

router = APIRouter()

def _council_id_from_request(request: Request) -> str | None:
    if not getattr(settings, 'council_scoping_enabled', False):
        return None
    # prefer session user if auth is enabled
    if settings.AUTH_ENABLED:
        user = request.session.get("user")
        if user and user.get("council_id"):
            return user["council_id"]
    # else, fall back to header
    hdr = settings.council_header
    return request.headers.get(hdr)

@router.get("/la/matters/list")
def list_matters(request: Request):
    cid = _council_id_from_request(request)
    with SessionLocal() as s:
        q = select(Matters).order_by(desc(Matters.id))
        if cid:
            q = q.where(Matters.council_id == cid)
        rows = s.execute(q).scalars().all()
        return {"matters": [{"id": m.id, "ref": m.ref, "created_at": m.created_at, "status": getattr(m,"status","done")} for m in rows]}

@router.post("/la/matters/ingest")
def ingest_matter(request: Request, ref: str = Form(None)):
    cid = _council_id_from_request(request)
    with SessionLocal() as s:
        if ref:
            m = s.query(Matters).filter(Matters.ref == ref).first()
            if m:
                if cid and m.council_id and m.council_id != cid:
                    raise HTTPException(403, "Matter belongs to another council")
                return {"matter": {"id": m.id, "ref": m.ref, "created_at": m.created_at}}
        m = Matters(ref=ref or "AUTO", created_at=None, council_id=cid, status="done")
        s.add(m); s.commit(); s.refresh(m)
        return {"matter": {"id": m.id, "ref": m.ref, "created_at": m.created_at}}

@router.get("/la/matters/{mid}/detail")
def matter_detail(mid: int, request: Request):
    cid = _council_id_from_request(request)
    with SessionLocal() as s:
        m = s.get(Matters, mid)
        if not m: raise HTTPException(404, "Not found")
        if cid and m.council_id and m.council_id != cid: raise HTTPException(403, "Forbidden")
        finds = s.query(Findings).filter(Findings.matter_id==mid).all()
        risks  = s.query(Risks).filter(Risks.matter_id==mid).all()
        return {
            "matter": {"id": m.id, "ref": m.ref, "created_at": m.created_at},
            "risks": [{"code": r.code, "level": r.level} for r in risks],
            "findings": [{"kind": f.kind, "value": f.value} for f in finds],
        }

@router.get("/la/matters/{mid}/report.docx")
def matter_report(mid: int, request: Request):
    cid = _council_id_from_request(request)
    with SessionLocal() as s:
        m = s.get(Matters, mid)
        if not m: raise HTTPException(404, "Not found")
        if cid and m.council_id and m.council_id != cid: raise HTTPException(403, "Forbidden")
    path = _call_build_docx(mid)
    return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=f"LA-Report-{mid}.docx")

@router.get("/la/matters/{mid}/export.json")
def matter_export(mid: int, request: Request):
    cid = _council_id_from_request(request)
    with SessionLocal() as s:
        m = s.get(Matters, mid)
        if not m: raise HTTPException(404, "Not found")
        if cid and m.council_id and m.council_id != cid: raise HTTPException(403, "Forbidden")
    return JSONResponse(_call_build_json(mid))


def _safe_get(obj, name, default):
    try:
        return getattr(obj, name)
    except Exception:
        return default
