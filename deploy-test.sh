#!/bin/bash
# Domus Planning Platform - Deployment Test Script
# Tests local functionality and provides deployment guidance

echo "🚀 Domus Planning Platform - Deployment Test"
echo "=============================================="

# Use virtual environment Python
PYTHON_CMD=".venv/bin/python"

# Test 1: Check Python environment
echo "1. Testing Python environment..."
$PYTHON_CMD -c "import fastapi, uvicorn; print('✅ Dependencies available')" || {
    echo "❌ Missing dependencies in venv"
    exit 1
}

# Test 2: Test app import
echo "2. Testing app import..."
$PYTHON_CMD -c "from main import app; print('✅ App imports successfully')" || {
    echo "❌ App import failed"
    exit 1
}

# Test 3: Start server and test endpoints
echo "3. Starting test server..."
$PYTHON_CMD -m uvicorn main:app --host 127.0.0.1 --port 8001 &
SERVER_PID=$!
sleep 3

# Test endpoints
echo "4. Testing endpoints..."
curl -s http://127.0.0.1:8001/ 
echo ""
curl -s http://127.0.0.1:8001/health
echo ""

# Cleanup
kill $SERVER_PID 2>/dev/null

echo "✅ Local testing complete!"
echo ""
echo "🌐 Deployment Options:"
echo "1. Render: https://render.com (connect GitHub repo manually)"
echo "2. Railway: https://railway.app (connect GitHub repo)"
echo "3. Fly.io: flyctl deploy (if fly CLI installed)"
echo "4. Vercel: vercel deploy (if vercel CLI installed)"
echo ""
echo "📋 Your app is ready for deployment with:"
echo "- Start command: uvicorn main:app --host 0.0.0.0 --port \$PORT"
echo "- Health check: /health"
echo "- Requirements: fastapi uvicorn"