from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {
        "message": "🚀 Domus Planning Platform is LIVE!", 
        "status": "working",
        "environment": "production",
        "deploy_time": "2025-10-01"
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "domus-planning-platform"}

# This is what Render will call
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)