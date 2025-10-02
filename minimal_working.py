from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os

app = FastAPI(title="Domus Planning Platform", version="2.0.0")

@app.get("/")
async def root():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>🏠 Domus Planning Platform</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
            max-width: 600px;
            text-align: center;
        }
        .logo { 
            font-size: 3rem; 
            font-weight: bold; 
            color: #1e40af; 
            margin-bottom: 1rem; 
        }
        .tagline { 
            font-size: 1.3rem; 
            color: #64748b; 
            margin-bottom: 2rem; 
        }
        .features {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin: 2rem 0;
        }
        .feature {
            padding: 1.5rem;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            transition: all 0.3s ease;
        }
        .feature:hover {
            border-color: #1e40af;
            transform: translateY(-2px);
        }
        .feature h3 {
            color: #1e40af;
            margin-bottom: 0.5rem;
            font-size: 1.1rem;
        }
        .feature p {
            color: #64748b;
            font-size: 0.9rem;
        }
        .cta {
            background: #1e40af;
            color: white;
            padding: 1rem 2rem;
            border: none;
            border-radius: 12px;
            font-size: 1.1rem;
            cursor: pointer;
            margin-top: 2rem;
            transition: all 0.3s ease;
        }
        .cta:hover {
            background: #1e3a8a;
            transform: translateY(-2px);
        }
        .status {
            margin-top: 2rem;
            padding: 1rem;
            background: #f0f9ff;
            border-radius: 12px;
            border-left: 4px solid #1e40af;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🏠 Domus Planning Platform</div>
        <div class="tagline">Professional Planning Intelligence & Compliance Automation</div>
        
        <div class="features">
            <div class="feature">
                <h3>🤖 AI Planning</h3>
                <p>Intelligent site analysis and approval prediction</p>
            </div>
            <div class="feature">
                <h3>📊 BNG Marketplace</h3>
                <p>Biodiversity Net Gain trading platform</p>
            </div>
            <div class="feature">
                <h3>⚡ Real-time Data</h3>
                <p>Property and planning intelligence</p>
            </div>
            <div class="feature">
                <h3>📝 Auto-Docs</h3>
                <p>Professional document generation</p>
            </div>
        </div>
        
        <button class="cta" onclick="alert('Platform is live and ready!')">🚀 Access Platform</button>
        
        <div class="status">
            <strong>✅ Platform Status:</strong> LIVE & OPERATIONAL<br>
            <small>Professional planning tools ready for use</small>
        </div>
    </div>
</body>
</html>
""")

@app.get("/test")
async def test():
    return {"status": "NEW VERSION WORKING", "timestamp": "2025-10-02", "platform": "Railway Fixed"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "platform": "Domus Planning Platform",
        "version": "2.0.0",
        "features": [
            "AI Planning Analysis",
            "BNG Marketplace", 
            "Auto-Docs Generation",
            "Property Data API"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("minimal_working:app", host="0.0.0.0", port=port)