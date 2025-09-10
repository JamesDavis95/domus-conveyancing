from fastapi import APIRouter
from fastapi.responses import JSONResponse

def apply(app):
    # Mount UI router (already present in la/ui.py)
    try:
        from la.ui import router as ui_router
        app.include_router(ui_router)
    except Exception as e:
        print("[warn] la.ui not mounted:", e)

    # Try to mount your real matters router
    try:
        from la.matters import router as matters_router
        app.include_router(matters_router)
        print("[ok] mounted la.matters router")
        return
    except Exception as e:
        print("[warn] la.matters not found, enabling shim:", e)

    # Minimal shim so the UI works until real router is present
    shim = APIRouter()
    _MATTERS = []

    @shim.get("/la/matters/list")
    def list_matters():
        return {"matters": _MATTERS}

    @shim.post("/la/matters/ingest")
    def ingest():
        mid = len(_MATTERS) + 1
        m = {"id": mid, "ref": f"MAT-{mid:04d}", "created_at": "now"}
        _MATTERS.append(m)
        return {"matter": m}

    @shim.get("/la/matters/{mid}/detail")
    def detail(mid: int):
        return {"risks": [], "findings": []}

    @shim.get("/la/matters/{mid}/report.docx")
    def report(mid: int):
        return JSONResponse({"ok": True, "hint": "Report generation handled by real router in la.matters"})

    @shim.get("/la/matters/{mid}/export.json")
    def export(mid: int):
        return JSONResponse({"ok": True, "hint": "JSON export handled by real router in la.matters"})

    app.include_router(shim)
    print("[ok] shim router mounted for /la/matters/*")
