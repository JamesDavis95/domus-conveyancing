#!/usr/bin/env python3
"""
Minimal app version that skips problematic imports for deployment
"""
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse

# Simple FastAPI app
app = FastAPI(title="Domus Global - Conveyancing Platform")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
except Exception as e:
    logging.warning(f"Could not mount static files: {e}")

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "Domus Global Platform is running!", "status": "healthy", "version": "1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "platform": "Domus Global"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)