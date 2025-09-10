import logging
from fastapi import FastAPI

# 1) Import your base FastAPI app
try:
    from main import app as base_app  # change if your entry file isn't main.py
except Exception as e:
    raise RuntimeError(f"Failed to import 'app' from main.py: {e}")

# 2) Attach security middleware if available
try:
    from security_core import attach_security  # type: ignore
except Exception:
    attach_security = None  # type: ignore

if attach_security:
    try:
        attach_security(base_app)
    except Exception as e:
        logging.getLogger("app_secured").warning("attach_security failed: %s", e)

# 3) Include the compatibility API router if present
try:
    from api_compat import router as compat_router  # type: ignore
    base_app.include_router(compat_router)
except Exception as e:
    logging.getLogger("app_secured").warning("compat router not loaded: %s", e)

# 4) Include approvals API router if present
try:
    from approvals import router as approvals_router  # type: ignore
    base_app.include_router(approvals_router)
except Exception as e:
    logging.getLogger("app_secured").warning("approvals router not loaded: %s", e)

# 5) Expose secured app
# ---- ensure main API is mounted under /api ----

# --- runtime safety for missing council settings ---
try:
    from settings import settings as _settings
    if not hasattr(_settings, "council_scoping_enabled"):
        setattr(_settings, "council_scoping_enabled", False)
    if not hasattr(_settings, "default_council_id"):
        setattr(_settings, "default_council_id", "E07000123")
except Exception:
    pass

# --- hotfix: guard council scoping for LA ingest ---
try:
    import logging
    from settings import settings as _settings
    import la.matters as _la_matters
    def _safe_council_id_from_request(request):
        try:
            enabled = getattr(_settings, "council_scoping_enabled", False)
            default = getattr(_settings, "default_council_id", "E07000123")
            if enabled:
                cid = (request.headers.get("X-Council-Id")
                       or request.query_params.get("council_id")
                       or default)
                return cid
            return default
        except Exception as e:
            logging.getLogger("hotfix").warning("council id defaulted: %s", e)
            return "E07000123"
    _la_matters._council_id_from_request = _safe_council_id_from_request
except Exception as _e:
    import logging as _log
    _log.getLogger("hotfix").warning("failed to patch la.matters: %s", _e)

app: FastAPI = base_app
