from fastapi import APIRouter
from fastapi.responses import JSONResponse

def apply(app):
    # UI router (already created earlier)
    try:
        from la.ui import router as ui_router
        app.include_router(ui_router)
    except Exception as e:
        print("[warn] la.ui not mounted:", e)

    # Primary LA matters router (expected by handover)
    mounted = False
    try:
        from la.matters import router as matters_router  # your existing router, if present
        app.include_router(matters_router)
        mounted = True
    except Exception as e:
        print("[warn] la.matters not found, enabling shim:", e)

    # If not present, install a minimal shim so UI doesn't 404
    if not mounted:
        shim = APIRouter()

        _MATTERS = []
        _ID = 0

        @shim.get("/la/matters/list")
        def list_matters():
            return {"matters": _MATTERS}

        @shim.post("/la/matters/ingest")
        def ingest():
            nonlocal_vars = {"_ID": len(_MATTERS) + 1}
            m = {"id": nonlocal_vars["_ID"], "ref": f"MAT-{nonlocal_vars['_ID']:04d}", "created_at": "now"}
            _MATTERS.append(m)
            return {"matter": m}

        @shim.get("/la/matters/{mid}/detail")
        def detail(mid: int):
            # Return empty risks/findings so UI renders
            return {"risks": [], "findings": []}

        @shim.get("/la/matters/{mid}/report.docx")
        def report(mid: int):
            return JSONResponse({"ok": True, "hint": "Report generation handled by real router in la.matters"})

        @shim.get("/la/matters/{mid}/export.json")
        def export(mid: int):
            return JSONResponse({"ok": True, "hint": "JSON export handled by real router in la.matters"})

        app.include_router(shim)
