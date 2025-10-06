"""
Domus AI - AI-Powered Development Intelligence Platform
Clean, working FastAPI application with full Domus AI features
"""

import os
import subprocess
from datetime import datetime

# Load environment variables first (production vs development)
ENV = os.getenv("ENVIRONMENT", "development")
if ENV != "production":
    # Try to load dotenv if available for development
    try:
        from dotenv import load_dotenv
        if os.path.exists('.env.production'):
            load_dotenv('.env.production')
            print("Loaded .env.production environment")
        elif os.path.exists('.env.local'):
            load_dotenv('.env.local')
            print("Loaded .env.local environment")
    except ImportError:
        # dotenv not available, use system environment
        pass
else:
    print("Production environment detected - using Render environment variables")

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

# Create FastAPI app
app = FastAPI(
    title="Domus AI",
    description="AI-Powered Development Intelligence Platform",
    version="1.0.0"
)

# Set up static build ID for cache busting
try:
    result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                          capture_output=True, text=True, timeout=5)
    static_build_id = result.stdout.strip() if result.returncode == 0 else 'dev'
    app.state.static_build_id = static_build_id
    print(f"✓ Static build ID: {static_build_id}")
except:
    static_build_id = 'dev'
    app.state.static_build_id = static_build_id
    print(f"✗ Git not available, using build ID: {static_build_id}")

# Mount static files if directory exists
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates if directory exists
if os.path.exists("templates"):
    templates = Jinja2Templates(directory="templates")
    templates_available = True
else:
    templates_available = False

# Core Domus AI routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Domus AI Dashboard - Main Platform"""
    if templates_available:
        return templates.TemplateResponse("simple_dashboard.html", {
            "request": request,
            "title": "Domus AI Dashboard",
            "static_build_id": static_build_id,
        })
    else:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html><head><title>Domus AI</title></head>
        <body><h1>🚀 Domus AI Platform</h1>
        <p>AI-Powered Development Intelligence is live!</p>
        <a href="/api/dashboard/kpis">Dashboard API</a> | 
        <a href="/api/sites">Sites API</a> | 
        <a href="/health">Health</a>
        </body></html>
        """)

@app.get("/dashboard", response_class=HTMLResponse) 
async def dashboard(request: Request):
    """Domus AI Dashboard"""
    if templates_available:
        return templates.TemplateResponse("simple_dashboard.html", {
            "request": request,
            "title": "Domus AI Dashboard",
            "static_build_id": static_build_id,
        })
    else:
        return HTMLResponse("<h1>Domus AI Dashboard</h1><p>Professional development intelligence platform</p>")

@app.get("/sites", response_class=HTMLResponse)
async def sites(request: Request):
    """Sites Management"""
    if templates_available:
        return templates.TemplateResponse("simple_sites.html", {
            "request": request,
            "title": "Sites - Domus AI",
            "static_build_id": static_build_id,
        })
    else:
        return HTMLResponse("<h1>Domus AI Sites</h1><p>Development site management</p>")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        timestamp = datetime.now().isoformat()
    except:
        timestamp = "unknown"
    
    return {
        "ok": True,
        "status": "healthy",
        "version": static_build_id,
        "env": os.getenv("ENVIRONMENT", "production"),
        "platform": "domus-ai",
        "timestamp": timestamp
    }

@app.get("/api/dashboard/kpis") 
async def dashboard_kpis():
    """Dashboard KPIs for Domus AI"""
    return {
        "active_sites": 3,
        "completed_this_month": 1, 
        "recent_activity": 12,
        "ai_credits_remaining": 100,
        "success_rate": 94,
        "esg_score": "A+"
    }

@app.get("/api/sites")
async def sites_api():
    """Sites API for Domus AI"""
    return {
        "sites": [
            {
                "id": 1,
                "name": "Kings Cross Development", 
                "address": "123 Kings Cross Road, London",
                "status": "analyzing",
                "ai_score": 78,
                "created_at": "2024-12-01T10:00:00",
                "updated_at": "2024-12-16T15:30:00"
            },
            {
                "id": 2,
                "name": "Canary Wharf Tower",
                "address": "456 Canary Wharf, London",
                "status": "approved", 
                "ai_score": 92,
                "created_at": "2024-11-15T09:15:00",
                "updated_at": "2024-12-10T14:20:00"
            },
            {
                "id": 3,
                "name": "Shoreditch Mixed Use",
                "address": "789 Shoreditch High Street, London",
                "status": "planning",
                "ai_score": 85,
                "created_at": "2024-12-05T14:30:00", 
                "updated_at": "2024-12-15T11:45:00"
            }
        ]
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    print(f"🚀 Domus AI starting up")
    print(f"   Version: {static_build_id}")
    print(f"   Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"   Platform: AI-Powered Development Intelligence")
    print(f"   Templates: {'Available' if templates_available else 'Fallback mode'}")

# Catch-all route (must be last)
@app.get("/{path:path}")
async def catch_all(path: str):
    """Catch-all route that returns 404"""
    raise HTTPException(status_code=404, detail=f"Path '/{path}' not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))