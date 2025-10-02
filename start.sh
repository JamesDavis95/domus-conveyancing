#!/bin/bash
echo "🚨 FIXED: Starting app.py with platform_production.html"
echo "PORT: $PORT"
echo "Current directory: $(pwd)"
echo "Files in directory:"
ls -la *.py
PORT=${PORT:-8000}
echo "🚀 Starting uvicorn with app:app on port $PORT"
exec uvicorn app:app --host 0.0.0.0 --port $PORT
