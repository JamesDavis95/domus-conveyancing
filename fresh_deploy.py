"""
Fresh deployment file to force Render cache clear
This will ensure the correct content is served
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from datetime import datetime

# Fresh app instance
app = FastAPI(title="Domus Fresh Deploy", version="FRESH-2025-10-02")

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_fresh():
    """Fresh deployment - serve correct HTML"""
    html_file = Path(__file__).parent / "frontend" / "platform_production.html"
    
    if html_file.exists():
        content = html_file.read_text(encoding='utf-8')
        
        # Inject fresh deployment marker
        content = content.replace(
            "<!-- CACHE BUST:", 
            f"<!-- FRESH DEPLOY {datetime.now().isoformat()} - CACHE BUST:"
        )
        
        return HTMLResponse(
            content=content,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
                "X-Fresh-Deploy": "2025-10-02",
                "X-Content-Source": "platform_production.html"
            }
        )
    else:
        return HTMLResponse("<h1>HTML file not found</h1>", status_code=404)

@app.get("/health")
async def health():
    return {
        "status": "FRESH-DEPLOYMENT",
        "version": "FRESH-2025-10-02", 
        "timestamp": datetime.now().isoformat(),
        "source": "fresh_deploy.py"
    }

@app.get("/debug")
async def debug():
    """Debug endpoint to verify file content"""
    html_file = Path(__file__).parent / "frontend" / "platform_production.html"
    if html_file.exists():
        content = html_file.read_text(encoding='utf-8')
        dashboard_start = content.find('<div id="dashboard"')
        dashboard_end = content.find('</div>', dashboard_start + 100)
        if dashboard_start != -1:
            preview = content[dashboard_start:dashboard_end+6]
            return {"dashboard_preview": preview}
    return {"error": "Cannot read file"}