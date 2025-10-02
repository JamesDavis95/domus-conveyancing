# Temporary bridge file for Render deployment
# This imports our main app.py to fix deployment issues

from app import app

# Re-export the FastAPI app
__all__ = ["app"]