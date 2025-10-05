#!/bin/bash

# Production Database Migration Script
# Run this after successful deployment to set up the database schema

echo "🗄️  Production Database Migration"
echo "================================="
echo ""

# Step 1: Check current migration status
echo "1. Checking current Alembic revision..."
alembic current

echo ""
echo "2. Showing pending migrations..."
alembic history --verbose

echo ""
echo "3. Running database migrations..."
# Run all pending migrations
alembic upgrade head

echo ""
echo "4. Verifying migration completion..."
alembic current

echo ""
echo "5. Creating initial admin user (if needed)..."
python init_production_db.py

echo ""
echo "✅ Production database migration completed!"
echo ""
echo "Next steps:"
echo "- Verify app health at https://your-app.onrender.com/health"
echo "- Test login functionality"
echo "- Confirm professional UI loads correctly"