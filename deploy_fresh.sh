#!/bin/bash
# Fresh Railway Deployment Script

echo "🚀 Creating fresh Railway deployment..."

# Make sure we're in the right directory
cd /Users/jamesdavis/Desktop/domus-conveyancing

echo "📦 Current files ready for deployment:"
echo "✅ minimal_working.py"
echo "✅ start.sh" 
echo "✅ requirements.txt"
echo "✅ railway.json"

echo ""
echo "🔧 To deploy to Railway:"
echo "1. Go to railway.app"
echo "2. Create NEW project"
echo "3. Connect to GitHub repo: JamesDavis95/domus-conveyancing"
echo "4. Set start command: bash start.sh"
echo "5. Deploy!"

echo ""
echo "🧪 Testing local version first..."
echo "Starting server on http://localhost:8000"

# Kill any existing servers
pkill -f uvicorn 2>/dev/null || true

# Start the server
python3 -m uvicorn minimal_working:app --host 0.0.0.0 --port 8000 --reload &

echo "⏳ Waiting 3 seconds for server to start..."
sleep 3

echo "🧪 Testing endpoints..."
curl -s http://localhost:8000/ | head -5
echo ""
echo "🧪 Test endpoint:"
curl -s http://localhost:8000/test
echo ""
echo "🧪 Health check:"
curl -s http://localhost:8000/health

echo ""
echo "✅ Local server is working!"
echo "Now deploy to Railway using the steps above."