import os, uuid, json, sqlite3, secrets, hashlib
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Request, HTTPException, Body, Depends, Header
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

DATA_DIR = Path("/data"); DB_PATH = DATA_DIR/"domus.db"; UPLOAD_DIR = DATA_DIR/"uploads"; FRONTEND_DIR = Path(__file__).parent/"frontend"
DATA_DIR.mkdir(parents=True, exist_ok=True); UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Domus Conveyancing – Rescue")

def _conn():
    conn = sqlite3.connect(str(DB_PATH)); conn.row_factory = sqlite3.Row; return conn
def _exec(sql, params=()): 
    with _conn() as c: c.execute(sql, params); c.commit()
def _q(sql, params=(), one=False):
    with _conn() as c:
        cur = c.execute(sql, params); row = cur.fetchone() if one else cur.fetchall()
        return dict(row) if row and one else [dict(r) for r in row]

def _init_db():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS orgs(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE,api_key TEXT UNIQUE,created_at TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS matters(id INTEGER PRIMARY KEY AUTOINCREMENT,org_id INTEGER,ref TEXT UNIQUE,spine_json TEXT,created_at TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY AUTOINCREMENT,org_id INTEGER,matter_id INTEGER,uuid TEXT,filename TEXT,content_type TEXT,size_bytes INTEGER,stored_path TEXT,kind TEXT,created_at TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS risks(id INTEGER PRIMARY KEY AUTOINCREMENT,org_id INTEGER,matter_id INTEGER,severity TEXT,code TEXT,title TEXT,detail TEXT,source_doc_id INTEGER,created_at TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS enquiries(id INTEGER PRIMARY KEY AUTOINCREMENT,org_id INTEGER,matter_id INTEGER,risk_id INTEGER,prompt TEXT,draft_text TEXT,status TEXT,created_at TEXT)""")
        c.commit()
_init_db()

if FRONTEND_DIR.exists(): app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=False), name="app")

@app.get("/") 
def root(): return FileResponse(str(FRONTEND_DIR/"index.html")) if (FRONTEND_DIR/"index.html").exists() else PlainTextResponse("Up")

@app.get("/healthz") 
def healthz(): return {"status":"ok"}

@app.get("/api/ping") 
def ping(): return {"pong":True}

# --- Auth ---
class AuthedOrg(BaseModel): id:int; name:str; api_key:str
def _org_by_key(k): return _q("SELECT * FROM orgs WHERE api_key=?",(k,),one=True)
async def require_org(x_api_key: str|None=Header(default=None,alias="X-Api-Key"))->AuthedOrg:
    if not x_api_key: raise HTTPException(401,"Missing X-Api-Key")
    row=_org_by_key(x_api_key)
    if not row: raise HTTPException(401,"Invalid API key")
    return AuthedOrg(**row)

# --- Orgs ---
class OrgCreate(BaseModel): name:str=Field(min_length=2,max_length=80)
@app.post("/api/orgs")
def create_org(p:OrgCreate):
    k=secrets.token_urlsafe(32)
    _exec("INSERT INTO orgs(name,api_key,created_at) VALUES(?,?,?)",(p.name,k,datetime.utcnow().isoformat()+"Z"))
    return {"ok":True,"org":_org_by_key(k)}

# --- Matters + spine ---
def nowz(): return datetime.utcnow().isoformat()+"Z"
def _new_spine(ref): return {"matter":{"ref":ref,"status":"open"},"docs":[],"risks":[],"timeline":[]}
def _spine_read(mid): r=_q("SELECT spine_json FROM matters WHERE id=?",(mid,),one=True); return json.loads(r["spine_json"]) if r else None
def _spine_write(mid,spine): _exec("UPDATE matters SET spine_json=? WHERE id=?",(json.dumps(spine),mid))

@app.post("/api/matters")
def create_matter(payload:dict=Body(...), org:AuthedOrg=Depends(require_org)):
    ref=payload.get("ref") or f"DMS/{datetime.utcnow().strftime('%Y%m%d')}/{uuid.uuid4().hex[:6].upper()}"
    spine=_new_spine(ref)
    _exec("INSERT INTO matters(ref,spine_json,created_at,org_id) VALUES(?,?,?,?)",(ref,json.dumps(spine),nowz(),org.id))
    m=_q("SELECT * FROM matters WHERE ref=?",(ref,),one=True)
    return {"ok":True,"matter":m}

@app.post("/api/matters/{mid}/upload")
async def upload(mid:int,file:UploadFile=File(...),kind:str="unknown",org:AuthedOrg=Depends(require_org)):
    b=await file.read()
    if len(b)>10*1024*1024: raise HTTPException(413,"Too big")
    u=uuid.uuid4().hex; path=UPLOAD_DIR/f"{u}__{file.filename}"
    with open(path,"wb") as f: f.write(b)
    _exec("INSERT INTO documents(matter_id,uuid,filename,content_type,size_bytes,stored_path,kind,created_at,org_id) VALUES(?,?,?,?,?,?,?,?,?)",
          (mid,u,file.filename,file.content_type,len(b),str(path),kind,nowz(),org.id))
    doc=_q("SELECT id,uuid,filename FROM documents WHERE uuid=?",(u,),one=True)
    sp=_spine_read(mid); sp["docs"].append(doc); _spine_write(mid,sp)
    return {"ok":True,"doc":doc}


@app.post("/api/matters/{mid}/risk-scan")
def risk(mid:int, doc_id:int = Body(..., embed=True), org:AuthedOrg = Depends(require_org)):
    # Validate doc belongs to matter
    doc = _q("SELECT * FROM documents WHERE id=? AND matter_id=?", (doc_id, mid), one=True)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found for matter")

    # Generate risks (stub; replace with real parser later)
    fname = (doc["filename"] or "").lower()
    candidates = []
    if "drain" in fname or "search" in fname:
        candidates.append(("medium","DRAINAGE_CAVEAT","Drainage/adoption caveat","Local search suggests drainage caveat; seek evidence of adoption.", doc_id))
    if "flood" in fname:
        candidates.append(("medium","FLOOD_MED","Medium flood risk","EA surface water zone; consider indemnity.", doc_id))
    if doc["size_bytes"] and doc["size_bytes"] > 2_000_000:
        candidates.append(("low","LARGE_DOC","Large document","Embedded images/annexes may require manual review.", doc_id))
    if not candidates:
        candidates.append(("low","NO_OBVIOUS","No obvious risks","", doc_id))

    created_ids = []
    # Insert risks in a single connection so last_insert_rowid works correctly
    with _conn() as c:
        for sev, code, title, detail, did in candidates:
            c.execute(
                "INSERT INTO risks(matter_id,severity,code,title,detail,source_doc_id,created_at,org_id) VALUES(?,?,?,?,?,?,?,?)",
                (mid, sev, code, title, detail, did, datetime.utcnow().isoformat()+"Z", org.id)
            )
            rid = c.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
            created_ids.append(rid)
        c.commit()

    # Update spine (append minimal risk entries + timeline)
    spine = _spine_read(mid)
    if spine is None:
        raise HTTPException(status_code=404, detail="Matter not found")
    for rid in created_ids:
        r = _q("SELECT id,severity,code,title,detail,source_doc_id,created_at FROM risks WHERE id=?", (rid,), one=True)
        spine["risks"].append(r)
    spine["timeline"].append({"t": datetime.utcnow().isoformat()+"Z", "event": "risk_scan", "doc_id": doc_id, "risks": created_ids})
    _spine_write(mid, spine)

    return {"ok": True, "added": created_ids}

@app.get("/api/matters/{mid}")
def get_matter(mid:int,org:AuthedOrg=Depends(require_org)):
    m=_q("SELECT * FROM matters WHERE id=?",(mid,),one=True)
    if not m: raise HTTPException(404,"Not found")
    sp=json.loads(m["spine_json"])
    return {"ok":True,"matter":m,"spine":sp}
