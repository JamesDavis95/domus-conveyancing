from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from datetime import datetime
import os

print("🚀 MINIMAL DOMUS PLATFORM STARTING - BUILD 2025-10-02...")
print("   File: simple_main.py")
print("   No middleware, no complex dependencies")
print("   FORCE REBUILD DEPLOYMENT")

app = FastAPI(title="Domus Planning Platform", version="4.0.0")

@app.get("/")
def home():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>🏠 Domus Planning Platform</title>
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #667eea, #764ba2); color: white; text-align: center; padding: 50px; }
        .container { background: white; color: #333; padding: 40px; border-radius: 20px; max-width: 800px; margin: 0 auto; }
        .feature { background: #f8f9ff; padding: 20px; margin: 10px; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏠 Domus Planning Platform</h1>
        <p>AI Operating System for Planning Intelligence & Compliance Automation</p>
        
        <div class="feature">
            <h3>🤖 AI Planning Analysis</h3>
            <p>Intelligent site analysis with approval prediction</p>
        </div>
        
        <div class="feature">
            <h3>📊 BNG Marketplace</h3>
            <p>Biodiversity Net Gain trading platform</p>
        </div>
        
        <div class="feature">
            <h3>📝 Auto-Docs Generation</h3>
            <p>Professional document generation</p>
        </div>
        
        <div class="feature">
            <h3>👥 User Roles & Permissions</h3>
            <p>Multi-role access control system</p>
        </div>
        
        <p><strong>✅ Platform Status: LIVE & OPERATIONAL</strong></p>
    </div>
</body>
</html>""")

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "platform": "Domus Planning Platform",
        "file": "simple_main.py",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/test")
def test():
    return {
        "message": "SUCCESS - RENDER DEPLOYMENT WORKING", 
        "file": "simple_main.py", 
        "build": "2025-10-02",
        "status": "operational"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("simple_main:app", host="0.0.0.0", port=port)