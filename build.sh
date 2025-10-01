#!/bin/bash
# Render Build Script for Domus Planning Platform

echo "🚀 Building Domus Planning Platform for Production..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Initialize database (only if DATABASE_URL is available)
if [ ! -z "$DATABASE_URL" ]; then
    echo "🗄️ Initializing production database..."
    python init_render_database.py
else
    echo "⚠️ DATABASE_URL not set, skipping database initialization"
fi

echo "✅ Build complete!"