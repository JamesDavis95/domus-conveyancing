import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import PlainTextResponse, JSONResponse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

app = FastAPI(title="Domus Global")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key="your-secret-key-here")

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy"}

# Ready endpoint
@app.get("/ready")
async def ready():
    return {"status": "ready"}

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Domus Global API", "status": "running"}

# Static files
try:
    app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")
except Exception as e:
    logging.warning(f"Could not mount static files: {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)