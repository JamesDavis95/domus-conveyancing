"""
Domus Planning Platform - Main Entry Point
FORCED TO USE FRESH DEPLOY TO CLEAR CACHE
"""

# Import the fresh deployment app
from fresh_deploy import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)