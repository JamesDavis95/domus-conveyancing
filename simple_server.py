#!/usr/bin/env python3
"""
Minimal server startup for Render deployment
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app_secured:app",
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )