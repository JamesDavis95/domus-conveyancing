import os, logging, subprocess
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import PlainTextResponse, JSONResponse
from prometheus_client import (
    CollectorRegistry, CONTENT_TYPE_LATEST, generate_latest,
    multiprocess, REGISTRY
)

import logging, os
logging.basicConfig(level=os.getenv('LOG_LEVEL','INFO'), format='%(asctime)s %(levelname)s %(name)s: %(message)s')

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

app = FastAPI(title="Domus Conveyancing API")

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Universal request logger middleware
class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        logger = logging.getLogger("request.logger")
        body = await request.body()
        logger.info(f"REQUEST {request.method} {request.url.path}\nHeaders: {dict(request.headers)}\nBody (first 2048 bytes): {body[:2048]!r}")
        response = await call_next(request)
        return response

app.add_middleware(RequestLoggerMiddleware)

# ---- health / ready / metrics ----
@app.get("/health")
def health():
    return {"ok": True, "env": os.getenv("ENV", "dev")}

@app.get("/ready")
def ready():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"ok": True}
    except Exception as e:
        return JSONResponse({"ok": False, "error": "db"}, status_code=503)

@app.get("/metrics")
def metrics():
    try:
        mp_dir = os.getenv("PROMETHEUS_MULTIPROC_DIR")
        if mp_dir:
            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)
            output = generate_latest(registry)
        else:
            output = generate_latest(REGISTRY)
        return PlainTextResponse(content=output, media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logging.getLogger(__name__).exception("metrics failed: %s", e)
        return PlainTextResponse("# metrics error\n", status_code=500)

# ---- include optional routers if present (no hard dependency) ----
def _try_include(module_name: str, attr: str = "router"):
    try:
        mod = __import__(module_name, fromlist=[attr])
        r = getattr(mod, attr, None)
        if r is not None:
            app.include_router(r)
            logging.getLogger(__name__).info("Included router: %s.%s", module_name, attr)
    except Exception as e:
        logging.getLogger(__name__).info("Optional router %s not loaded: %s", module_name, e)

for candidate in ("api_compat", "la.matters", "la.workflow", "debug", "api_mount", "la.ui"):
    _try_include(candidate)

from api_compat import router as compat_router
app.include_router(compat_router)

app.mount("/app", StaticFiles(directory="frontend", html=True), name="app")

from starlette.responses import RedirectResponse
@app.get("/")
def root():
    return RedirectResponse("/app/platform.html")

@app.get("/platform")
def platform():
    return RedirectResponse("/app/platform.html")

@app.get("/favicon.ico")
def favicon():
    from starlette.responses import PlainTextResponse, JSONResponse
    return PlainTextResponse("", status_code=204)

from la.matters import router as la_router
app.include_router(la_router)

# NEW: Add spatial API endpoints
try:
    from la.spatial import router as spatial_router
    app.include_router(spatial_router)
    logger.info("Included router: la.spatial.router")
except (ImportError, OSError) as e:
    logger.warning(f"Optional router la.spatial not loaded: {e}")

# NEW: Phase 2A - Complete LA workflow system
from la.workflow import router as workflow_router
app.include_router(workflow_router)

# NEW: Enterprise Platform APIs
try:
    from enterprise_api import enterprise_router
    app.include_router(enterprise_router)
    logging.info("✅ Enterprise Platform APIs loaded")
except ImportError as e:
    logging.warning(f"❌ Enterprise APIs not available: {e}")

from db import init_db
import logging

@app.on_event("startup")
def _startup_init_db():
    try:
        init_db()
    except Exception as e:
        logging.getLogger(__name__).exception("DB init failed: %s", e)

from sqlalchemy import text
from db import engine

@app.get("/health/av")
def health_av():
    import os
    return {"clamav_enabled": os.getenv("CLAMAV_ENABLED","false").lower()=="true"}

@app.get("/health/storage")
def health_storage():
    import os
    ok = True
    detail = {}
    if os.getenv("S3_BUCKET"):
        # assume S3 configured; real check would HEAD the bucket
        detail["mode"] = "s3"
    else:
        detail["mode"] = "local"
        data_dir = os.getenv("DATA_DIR","./data/uploads")
        try:
            os.makedirs(data_dir, exist_ok=True)
            test = os.path.join(data_dir, ".writetest")
            with open(test,"wb") as f: f.write(b"ok")
            os.remove(test)
        except Exception as e:
            ok = False
            detail["error"] = str(e)
    return {"ok": ok, **detail}

app.add_middleware(SessionMiddleware, secret_key=os.getenv('SESSION_SECRET','dev-secret'), https_only=False)

app.add_middleware(CORSMiddleware, allow_origins=(os.getenv('PASSPORT_CORS_ORIGINS','').split(',') if os.getenv('PASSPORT_CORS_ORIGINS') else ['*']), allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

from authlib.integrations.starlette_client import OAuth
oauth = None
if os.getenv("OIDC_ENABLED","false").lower()=="true":
    oauth = OAuth()
    oauth.register(
        name="oidc",
        server_metadata_url=os.getenv("OIDC_DISCOVERY_URL",""),
        client_id=os.getenv("OIDC_CLIENT_ID",""),
        client_secret=os.getenv("OIDC_CLIENT_SECRET",""),
        client_kwargs={"scope": "openid email profile"},
    )

from fastapi import Request
@app.get("/login")
async def login(request: Request):
    if oauth is None: 
        return {"ok": False, "error": "OIDC disabled"}
    redirect_uri = os.getenv("OIDC_REDIRECT_URI", str(request.url_for("auth_callback")))
    return await oauth.oidc.authorize_redirect(request, redirect_uri)

@app.get("/auth/callback")
async def auth_callback(request: Request):
    if oauth is None: 
        return {"ok": False}
    token = await oauth.oidc.authorize_access_token(request)
    user = token.get("userinfo") or {}
    request.session["user"] = {"sub": user.get("sub"), "email": user.get("email")}
    return RedirectResponse("/")

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/public")

@app.middleware("http")
async def staff_guard(request: Request, call_next):
    if os.getenv("OIDC_ENABLED","false").lower()=="true":
        p = request.url.path
        staff_paths = ("/", "/app", "/app/", "/la", "/la/")
        if p == "/" or p.startswith(staff_paths):
            if not request.session.get("user"):
                # allow health/ready/metrics/public without login
                if p.startswith(("/health","/ready","/metrics","/public")):
                    return await call_next(request)
                return RedirectResponse("/login")
    return await call_next(request)

@app.get("/version")
def version():
    sha = "unknown"
    try:
        sha = subprocess.check_output(["git","rev-parse","--short","HEAD"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        pass
    return {"name":"Domus Conveyancing API","git_sha": sha, "env": os.getenv("ENV","dev")}
