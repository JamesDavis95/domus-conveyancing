#!/usr/bin/env python3
"""
Debug script to help identify deployment issues
"""
import sys
import os

print("=== DEPLOYMENT HEALTH CHECK ===")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"PORT environment variable: {os.environ.get('PORT', 'NOT SET')}")

# Test critical imports
try:
    import fastapi
    print("✅ FastAPI import successful")
except ImportError as e:
    print(f"❌ FastAPI import failed: {e}")

try:
    import uvicorn
    print("✅ Uvicorn import successful")
except ImportError as e:
    print(f"❌ Uvicorn import failed: {e}")

try:
    from app_secured import app
    print("✅ App import successful")
except ImportError as e:
    print(f"❌ App import failed: {e}")
    sys.exit(1)

# Test static files
frontend_path = "frontend"
if os.path.exists(frontend_path):
    print(f"✅ Frontend directory exists")
    files = os.listdir(frontend_path)
    print(f"Frontend files: {files}")
else:
    print("❌ Frontend directory missing")

print("=== HEALTH CHECK COMPLETE ===")