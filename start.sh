#!/bin/bash
echo "🚨 FIXED: Starting app.py with platform_production.html"
echo "PORT: $PORT"
echo "Current directory: $(pwd)"
echo "Files in directory:"
ls -la *.py
echo "Checking app.py import:"
python3 -c "from app import app; print('✅ app.py loaded successfully')"
echo "Checking HTML file:"
head -10 frontend/platform_production.html
PORT=${PORT:-8000}
echo "🚀 Starting uvicorn with app:app on port $PORT"
exec uvicorn app:app --host 0.0.0.0 --port $PORT
