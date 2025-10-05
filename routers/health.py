"""
Health check and diagnostics routes
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, HTMLResponse
import os
import subprocess
from datetime import datetime

router = APIRouter()

@router.head("/")
async def head_root():
    """Handle HEAD requests for health checks"""
    return HTMLResponse(
        "",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            "Surrogate-Control": "no-store"
        }
    )

@router.get("/health")
async def health_check():
    """Health check endpoint with system info"""
    try:
        # Get git version
        try:
            git_sha = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'], 
                capture_output=True, text=True, cwd=os.path.dirname(__file__)
            )
            version = git_sha.stdout.strip() if git_sha.returncode == 0 else "unknown"
        except:
            version = "unknown"
        
        return JSONResponse({
            "ok": True,
            "status": "healthy",
            "version": version,
            "env": os.getenv("ENVIRONMENT", "development"),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    except Exception as e:
        return JSONResponse(
            {
                "ok": False,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            status_code=500
        )