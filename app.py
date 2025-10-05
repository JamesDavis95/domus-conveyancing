"""
Domus - Professional Conveyancing Platform
Clean FastAPI application assembly according to specification
"""

import os
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from database_config import Base, engine

# Create FastAPI app
app = FastAPI(
    title="Domus",
    description="Professional Conveyancing Platform",
    version="1.0.0"
)

# Set up static build ID for cache busting
try:
    git_sha = subprocess.run(
        ['git', 'rev-parse', '--short', 'HEAD'], 
        capture_output=True, text=True, cwd=os.path.dirname(__file__)
    )
    static_build_id = git_sha.stdout.strip() if git_sha.returncode == 0 else "dev"
except:
    static_build_id = os.getenv("STATIC_BUILD_ID", "dev")

app.state.static_build_id = static_build_id

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
    print(f"✓ Database tables created/verified")
except Exception as e:
    print(f"✗ Database setup failed: {e}")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Import routers (order matters per specification)
from routers import public, health, dashboard
# TODO: Add remaining routers: auth, cases, documents, enterprise, users, roles, billing, settings, audit

# Include routers in correct order
app.include_router(public.router, tags=["public"])
app.include_router(health.router, tags=["health"])
app.include_router(dashboard.router, tags=["dashboard"])

# Catch-all route (must be last) - returns 404, never serves app shell
@app.get("/{path:path}")
async def catch_all(path: str):
    """Catch-all route that returns 404 - never serves app shell"""
    raise HTTPException(status_code=404, detail=f"Path '/{path}' not found")

# Startup event
@app.on_event("startup")
async def startup_event():
    print(f"🚀 Domus starting up")
    print(f"   Version: {static_build_id}")
    print(f"   Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"   Database: PostgreSQL via psycopg v3")
    print(f"   Static build ID: {static_build_id}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)