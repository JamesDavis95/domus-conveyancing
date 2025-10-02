"""
Domus Planning Platform - Main Entry Point
Fixed to serve the correct HTML content
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn
from datetime import datetime

# Create FastAPI app directly in main.py to ensure it works
app = FastAPI(title="Domus Planning Platform", version="4.1.0-CACHE-CLEARED")

# Serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the production platform interface with cache busting"""
    try:
        # Read the production HTML file
        html_path = Path(__file__).parent / "frontend" / "platform_production.html"
        if html_path.exists():
            with open(html_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            # Add cache-busting timestamp to the HTML
            timestamp = datetime.now().isoformat()
            html_content = html_content.replace(
                "<head>", 
                f'<head>\n    <!-- DEPLOYMENT TIMESTAMP: {timestamp} -->'
            )
            
            return HTMLResponse(
                content=html_content,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache", 
                    "Expires": "0"
                }
            )
        else:
            return "<h1>Error: platform_production.html not found</h1>"
    except Exception as e:
        return f"<h1>Error loading HTML: {str(e)}</h1>"

@app.get("/health")
async def health_check():
    """Simple health check"""
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "platform": "Domus Planning AI System",
        "version": "4.1.0-CACHE-CLEARED",
        "file": "main.py",
        "deployment": "2025-10-02-21:05"
    }

@app.get("/debug-html")
async def debug_html():
    """Debug endpoint to check what HTML content is being served"""
    try:
        html_path = Path(__file__).parent / "frontend" / "platform_production.html"
        if html_path.exists():
            with open(html_path, 'r', encoding='utf-8') as file:
                content = file.read()
            # Return just the dashboard section
            start = content.find('<div id="dashboard" class="page active">')
            end = content.find('</div>', start + 200)
            if start != -1 and end != -1:
                return {"dashboard_content": content[start:end+6]}
            else:
                return {"error": "Dashboard section not found", "file_size": len(content)}
        else:
            return {"error": "HTML file not found", "path": str(html_path)}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)