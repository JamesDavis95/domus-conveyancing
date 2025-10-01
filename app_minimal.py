"""
Minimal FastAPI app for Render deployment testing
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Domus Planning Platform", version="1.0.0")

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Domus Planning Platform</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; 
                   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   color: white; min-height: 100vh; margin: 0; }
            .container { background: rgba(255,255,255,0.1); padding: 2rem; 
                        border-radius: 16px; backdrop-filter: blur(10px); }
            h1 { font-size: 3rem; margin-bottom: 1rem; }
            p { font-size: 1.2rem; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏠 Domus Planning Platform</h1>
            <p>Professional Planning Intelligence System</p>
            <p>✅ Successfully Deployed on Render</p>
            <p><strong>Next:</strong> Full platform deployment in progress...</p>
        </div>
    </body>
    </html>
    """

@app.get("/health")
async def health():
    return {"status": "ok", "platform": "Domus Planning Platform"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)