import sqlalchemy as sa
from fastapi import APIRouter, HTTPException, Request
from settings import settings

router = APIRouter(prefix="/api", tags=["approvals"])
engine = sa.create_engine(settings.DATABASE_URL)

# idempotent DDL
with engine.begin() as c:
    c.exec_driver_sql("""
    CREATE TABLE IF NOT EXISTS approvals (
      id SERIAL PRIMARY KEY,
      matter_id INTEGER NOT NULL,
      decided_at TIMESTAMP DEFAULT NOW(),
      decided_by VARCHAR(255),
      decision VARCHAR(32) NOT NULL
    )""")

@router.post("/matters/{mid}/approve")
def approve_matter(mid:int, request:Request):
    user = getattr(request.state, "user", {}) or {}
    who = user.get("id") or "unknown"
    with engine.begin() as c:
        # set status to 'approved' (column was ensured in your DB helper)
        c.exec_driver_sql("UPDATE matters SET status='approved' WHERE id=%s", (mid,))
        c.exec_driver_sql(
            "INSERT INTO approvals (matter_id, decided_by, decision) VALUES (%s,%s,'approved')",
            (mid, who)
        )
    return {"ok": True, "matter_id": mid, "status": "approved"}

@router.get("/matters/{mid}/approvals")
def list_approvals(mid:int):
    with engine.begin() as c:
        rows = c.exec_driver_sql("SELECT id, decided_at, decided_by, decision FROM approvals WHERE matter_id=%s ORDER BY decided_at DESC", (mid,))
        items = [
            {"id": r[0], "decided_at": str(r[1]), "decided_by": r[2], "decision": r[3]}
            for r in rows.fetchall()
        ]
    return {"items": items}
