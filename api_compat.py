from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Depends
import httpx, time, tempfile, os, logging
from pdfminer.high_level import extract_text
from redis import Redis
from settings import settings

router = APIRouter(prefix="/api", tags=["compat"])

def _redis() -> Redis:
    return Redis.from_url(settings.REDIS_URL)

def _fw_headers(request: Request):
    h = {}
    auth = request.headers.get("authorization")
    api = request.headers.get("x-api-key")
    if auth: h["authorization"] = auth
    if api: h["x-api-key"] = api
    return h

async def _get(path, request: Request):
    # For development/standalone mode, try localhost first, then original api host
    hosts = ["http://localhost:8000", "http://api:8000"]
    last_error = None
    
    for host in hosts:
        async with httpx.AsyncClient(timeout=30.0) as c:
            try:
                r = await c.get(f"{host}{path}", headers=_fw_headers(request))
                if r.status_code>=400: raise HTTPException(r.status_code, r.text)
                return r.json()
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_error = e
                continue
    
    # If all hosts failed, raise the last error
    if last_error:
        raise HTTPException(503, f"Service unavailable: {last_error}")
    raise HTTPException(503, "All API services unavailable")

async def _post(path, request: Request, **kw):
    # For development/standalone mode, try localhost first, then original api host  
    hosts = ["http://localhost:8000", "http://api:8000"]
    last_error = None
    
    for host in hosts:
        async with httpx.AsyncClient(timeout=60.0) as c:
            try:
                r = await c.post(f"{host}{path}", headers=_fw_headers(request), **kw)
                if r.status_code>=400: raise HTTPException(r.status_code, r.text)
                try: return r.json()
                except: return {"raw": r.text}
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_error = e
                continue
                
    # If all hosts failed, raise the last error
    if last_error:
        raise HTTPException(503, f"Service unavailable: {last_error}")
    raise HTTPException(503, "All API services unavailable")

@router.post("/orgs")
async def create_org_demo():
    return {"org":{"id":"demo","name":"Demo","api_key":"demo-key"}}

@router.post("/matters")
async def create_matter(request: Request):
    try:
        await _post("/la/matters/ingest", request)
        data = await _get("/la/matters/list", request)
        items = data.get("matters",[]) or []
        if not items: raise HTTPException(500,"No matters after ingest")
        last = items[-1]
        return {"matter":{"id":last.get("id"),"ref":last.get("ref")}}
    except Exception as e:
        logging.getLogger("api_compat").error("Error in create_matter: %s", e)
        raise

@router.get("/matters/{mid}")
async def get_matter(mid:int, request: Request):
    return await _get(f"/la/matters/{mid}/detail", request)

@router.post("/matters/{mid}/upload")
async def upload_pdf(mid:int, request: Request, kind:str="search", file:UploadFile=File(...), r:Redis=Depends(_redis)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400,"Only PDF supported")
    data = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        text = extract_text(tmp_path) or ""
    finally:
        try: os.unlink(tmp_path)
        except Exception: pass

    seq_key = f"pdftext:{mid}:seq"
    doc_id = int(r.incr(seq_key))
    key = f"pdftext:{mid}:{doc_id}"
    r.setex(key, 86400, text)

    msg = "Extracted text saved" if text.strip() else "No extractable text (image-only PDF?)"
    return {"ok": True, "doc": {"id": doc_id, "kind": kind, "filename": file.filename}, "message": msg}

@router.post("/matters/{mid}/risk-scan")
async def risk_scan(mid:int, body:dict, request: Request, r:Redis=Depends(_redis)):
    doc_id = body.get("doc_id")
    extracted_text = body.get("extracted_text") or body.get("text") or ""
    if doc_id and not extracted_text:
        val = r.get(f"pdftext:{mid}:{doc_id}")
        extracted_text = val.decode("utf-8") if val else ""

    detail = await _get(f"/la/matters/{mid}/detail", request)
    ref = (detail.get("matter") or {}).get("ref") or str(mid)
    if not extracted_text.strip():
        extracted_text = f"Search for matter {ref}. No PDF text captured."

    out = await _post("/api/process", request, data={"ref": ref, "llc1_text": extracted_text, "con29_text": ""})
    job_id = out.get("job_id")
    if not job_id:
        return {"ok": False, "message": "Processor did not return job_id", "raw": out}
    for _ in range(60):
        try:
            js = await _get(f"/jobs/{job_id}/status", request)
            if js.get("status") == "finished":
                break
        except HTTPException as e:
            if e.status_code == 404:
                logging.getLogger("api_compat").warning("Job %s status not found, continuing", job_id)
                break
            raise
        time.sleep(1)

    updated = await _get(f"/la/matters/{mid}/detail", request)
    return {"ok": True, "job_id": job_id, "matter": updated}

@router.get("/matters/{mid}/enquiries")
async def list_enquiries(mid:int):
    return {"items":[]}

@router.post("/enquiries/{eid}/promote")
async def promote_enquiry(eid:int, body:dict):
    return {"ok": True, "id": eid, "status": body.get("status","ready")}

@router.get("/passport/{mid}")
async def passport(mid:int, request: Request):
    d = await _get(f"/la/matters/{mid}/detail", request)
    return {"passport":{"ref": d.get("matter",{}).get("ref") or str(mid),
                        "risk_count": len(d.get("risks",[])),
                        "finding_count": len(d.get("findings",[])),
                        "risks": d.get("risks",[]),
                        "findings": d.get("findings",[]) }}
