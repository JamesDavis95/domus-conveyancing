#!/usr/bin/env python3
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Domus Global")

# Mount static files for CSS, JS, images
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    with open('frontend/platform.html', 'r') as f:
        return f.read()

@app.get("/health")
async def health():
    return {"status": "healthy", "platform": "Domus Global", "version": "1.0"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)