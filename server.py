#!/usr/bin/env python3
"""
Bulletproof startup script for Domus Planning Platform
Works on any cloud platform: Render, Railway, Heroku, etc.
"""
import os
import sys

print("🚀 Starting Domus Planning Platform...")

try:
    import uvicorn
    from main import app
    print("✅ Dependencies loaded successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

if __name__ == "__main__":
    # Get port from environment (Render, Railway, Heroku all use PORT)
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"🌐 Starting server on {host}:{port}")
    
    try:
        uvicorn.run(
            app, 
            host=host, 
            port=port,
            log_level="info",
            access_log=True
        )
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        sys.exit(1)