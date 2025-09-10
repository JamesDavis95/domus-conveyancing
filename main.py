from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST, multiprocess
# original: from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, CollectorRegistry, multiprocess
from starlette.middleware.sessions import SessionMiddleware

from settings import settings
from evidence import router as evidence_router
from la.matters import router as matters_router
from api import router as api_router

import sqlalchemy as sa, redis, boto3, socket

app = FastAPI(title="Domus Conveyancing API")
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

@app.get("/health")
def health():
    return {"ok": True, "env": settings.APP_ENV}

@app.get("/ready")
def ready():
    ok = True
    db_ok = redis_ok = s3_ok = clam_ok = False
    try:
        eng = sa.create_engine(settings.DATABASE_URL)
        with eng.connect() as c:
            c.execute(sa.text("SELECT 1"))
        db_ok = True
    except Exception:
        ok = False
    try:
        r = redis.from_url(settings.REDIS_URL); r.ping()
        redis_ok = True
    except Exception:
        ok = False
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
        )
        s3.list_buckets()
        s3_ok = True
    except Exception:
        ok = False
    try:
        sock = socket.create_connection((settings.CLAMAV_HOST, settings.CLAMAV_PORT), timeout=1.0)
        sock.close()
        clam_ok = True
    except Exception:
        ok = False
    return {"ok": ok, "db": db_ok, "redis": redis_ok, "s3": s3_ok, "clamav": clam_ok}

@app.get("/metrics")
def metrics():
    import os
    from fastapi import Response
    # Fallback: if PROMETHEUS_MULTIPROC_DIR unset, don't use multiprocess collector
    mp_dir = os.getenv("PROMETHEUS_MULTIPROC_DIR")
    if mp_dir and os.path.isdir(mp_dir):
        reg = CollectorRegistry()
        multiprocess.MultiProcessCollector(reg)
        payload = generate_latest(reg)
    else:
        # Use default REGISTRY when multiprocess disabled
        from prometheus_client import REGISTRY
        payload = generate_latest(REGISTRY)
    return Response(payload, media_type=CONTENT_TYPE_LATEST)

    multiprocess.MultiProcessCollector(registry)
    data = generate_latest(registry)
    return PlainTextResponse(data, media_type=CONTENT_TYPE_LATEST)

app.include_router(evidence_router)
app.include_router(matters_router)
app.include_router(api_router)
