#!/bin/bash
echo "🚨 DEPLOYMENT DEBUG: Starting minimal_working.py"
echo "PORT: $PORT"
echo "Current directory: $(pwd)"
echo "Files in directory:"
ls -la *.py
PORT=${PORT:-8000}
echo "🚀 Starting uvicorn with minimal_working:app on port $PORT"
exec uvicorn minimal_working:app --host 0.0.0.0 --port $PORT
