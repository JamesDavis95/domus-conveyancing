#!/usr/bin/env python3
"""
Render deployment startup script for Domus Planning Platform
Ensures proper initialization and error handling for cloud deployment
"""

import os
import sys
import traceback
from pathlib import Path

def main():
    """Main startup function with comprehensive error handling"""
    try:
        print("🚀 Starting Domus Planning Platform on Render...")
        
        # Set environment variables for production
        os.environ.setdefault('ENVIRONMENT', 'production')
        os.environ.setdefault('PYTHONPATH', str(Path(__file__).parent))
        
        # Import and start the app
        print("📦 Importing application...")
        from app import app
        print("✅ Application imported successfully")
        
        # Import uvicorn
        import uvicorn
        print("🌐 Starting web server...")
        
        # Get port from environment
        port = int(os.environ.get('PORT', 8000))
        host = "0.0.0.0"
        
        print(f"🎯 Server starting on {host}:{port}")
        
        # Start the server
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        print(f"❌ Fatal error during startup: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()