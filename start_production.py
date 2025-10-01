#!/usr/bin/env python3
"""
Production Startup Script
Simple script to launch the production platform
"""

import os
import subprocess
import sys

def start_production():
    """Start the production server"""
    
    print("🚀 Starting Domus Planning Platform - Production Mode")
    print("=" * 60)
    
    # Set environment variables
    os.environ["ENVIRONMENT"] = "production"
    os.environ["DATABASE_URL"] = "sqlite:///./production.db"
    
    # Check if database exists
    if not os.path.exists("production.db"):
        print("❌ Production database not found!")
        print("   Please run: python init_production_database.py")
        return
    
    print("✅ Database found")
    print("✅ Starting FastAPI server...")
    print("📡 Access your platform at: http://localhost:8000")
    print("🔧 Admin panel: http://localhost:8000/admin/docs")
    print("📧 Admin login: admin@domusplanning.co.uk / admin123!")
    print("⚠️  Remember to change the admin password!")
    print("=" * 60)
    
    # Start the server using the existing app.py
    try:
        python_exe = "/Users/jamesdavis/Desktop/domus-conveyancing/.venv/bin/python"
        subprocess.run([
            python_exe, "-m", "uvicorn", 
            "app:app",  # Use existing app.py
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ])
    except KeyboardInterrupt:
        print("\n🔄 Shutting down server...")
    except Exception as e:
        print(f"❌ Error starting server: {str(e)}")

if __name__ == "__main__":
    start_production()