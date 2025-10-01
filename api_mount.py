from fastapi import APIRouter
router = APIRouter()
@router.get("/api/example")
def example():
    return {"ok": True}
from fastapi import APIRouter, HTTPException
router = APIRouter()
try:
    from db import get_session, list_convey_searches
    @router.get("/api/list")
    def api_list():
        try:
            with get_session() as session:
                rows = list_convey_searches(session)
                out = []
                for r in rows or []:
                    out.append({
                        "id": getattr(r, "id", None),
                        "council": getattr(r, "council", None),
                        "risk_score": getattr(r, "risk_score", None),
                        "needs_review": bool(getattr(r, "needs_review", False)),
                        "created_at": str(getattr(r, "created_at", "")) if getattr(r, "created_at", None) else ""
                    })
                return out
        except Exception as e:
            return []
    @router.get("/api/review-queue")
    def api_review_queue():
        try:
            with get_session() as session:
                rows = list_convey_searches(session)
                out = []
                for r in rows or []:
                    if bool(getattr(r, "needs_review", False)):
                        out.append({
                            "id": getattr(r, "id", None),
                            "council": getattr(r, "council", None),
                            "risk_score": getattr(r, "risk_score", None),
                            "created_at": str(getattr(r, "created_at", "")) if getattr(r, "created_at", None) else ""
                        })
                return out
        except Exception as e:
            return []
except Exception:
    @router.get("/api/list")
    def api_list_unavailable():
        return []
    @router.get("/api/review-queue")
    def api_review_queue_unavailable():
        return []
from fastapi import APIRouter, HTTPException
router = APIRouter()
try:
    from db import get_session, list_convey_searches
    @router.get("/api/list")
    def api_list():
        try:
            with get_session() as session:
                rows = list_convey_searches(session)
                out = []
                for r in rows or []:
                    out.append({
                        "id": getattr(r, "id", None),
                        "council": getattr(r, "council", None),
                        "risk_score": getattr(r, "risk_score", None),
                        "needs_review": bool(getattr(r, "needs_review", False)),
                        "created_at": str(getattr(r, "created_at", "")) if getattr(r, "created_at", None) else ""
                    })
                return out
        except Exception as e:
            return []
    @router.get("/api/review-queue")
    def api_review_queue():
        try:
            with get_session() as session:
                rows = list_convey_searches(session)
                out = []
                for r in rows or []:
                    if bool(getattr(r, "needs_review", False)):
                        out.append({
                            "id": getattr(r, "id", None),
                            "council": getattr(r, "council", None),
                            "risk_score": getattr(r, "risk_score", None),
                            "created_at": str(getattr(r, "created_at", "")) if getattr(r, "created_at", None) else ""
                        })
                return out
        except Exception as e:
            return []
except Exception:
    @router.get("/api/list")
    def api_list_unavailable():
        return []
    @router.get("/api/review-queue")
    def api_review_queue_unavailable():
        return []
from fastapi import HTTPException
import sqlite3, os, time

@router.post("/api/volume-smoke")
def volume_smoke():
    try:
        db_path = "/data/domus.db"
        os.makedirs("/data", exist_ok=True)
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT)")
        k = f"smoke-{int(time.time())}"
        cur.execute("INSERT OR REPLACE INTO kv (k, v) VALUES (?, ?)", (k, "ok"))
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM kv")
        count = cur.fetchone()[0]
        conn.close()
        return {"db": db_path, "wrote": k, "rows": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import UploadFile, File
@router.post("/api/process")
async def process_upload(file: UploadFile = File(...)):
    data = {"filename": file.filename, "content_type": file.content_type}
    blob = await file.read()
    data["size_bytes"] = len(blob)
    return data
from fastapi import Request, Depends
from sqlalchemy.orm import Session
from stripe_integration import StripeService
from models import SessionLocal

# Dependency to get DB session
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/api/billing/checkout-session")
async def create_checkout_session(
    request: Request,
    org_id: int,
    plan_type: str,
    success_url: str,
    cancel_url: str,
    db: Session = Depends(get_db)
):
    """Create a Stripe Checkout Session and return the URL"""
    url = await StripeService.create_checkout_session(
        org_id=org_id,
        plan_type=plan_type,
        success_url=success_url,
        cancel_url=cancel_url,
        db=db
    )
    return {"checkout_url": url}
