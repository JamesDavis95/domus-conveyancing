"""
Ultra-minimal FastAPI app for Render deployment
"""
import os
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {
        "message": "🏠 Domus Planning Platform", 
        "status": "✅ WORKING ON RENDER!",
        "platform": "Professional Planning Intelligence"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)