"""
Domus Planning Platform - Main Entry Point
This ensures the correct app is served regardless of configuration
"""

from app import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)