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
            result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                                  capture_output=True, text=True, timeout=5)
            version = result.stdout.strip() if result.returncode == 0 else "unknown"
        except:
            version = "unknown"
        
        return {
            "ok": True,
            "status": "healthy",
            "version": version,
            "env": os.getenv("ENVIRONMENT", "production"),
            "timestamp": datetime.now().isoformat(),
            "platform": "domus-ai",
            "force_deploy": "2025-10-06-v2"  # Force deployment marker
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "status": "error", "error": str(e)}
        )