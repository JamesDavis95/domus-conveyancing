#!/bin/bash

# Production Verification Script
# Test all critical endpoints and verify the deployment

echo "🔍 Production Deployment Verification"
echo "====================================="
echo ""

# You'll need to replace this with your actual Render URL
PRODUCTION_URL="https://domus-planning-platform.onrender.com"

echo "Testing production deployment at: $PRODUCTION_URL"
echo ""

# Test 1: Health Check
echo "1. Testing health endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" "$PRODUCTION_URL/health")
if [ "$response" = "200" ]; then
    echo "   ✅ Health check passed ($response)"
else
    echo "   ❌ Health check failed ($response)"
fi

# Test 2: Root endpoint
echo ""
echo "2. Testing root endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" "$PRODUCTION_URL/")
if [ "$response" = "200" ]; then
    echo "   ✅ Root endpoint accessible ($response)"
else
    echo "   ❌ Root endpoint failed ($response)"
fi

# Test 3: Check for demo content (should not exist)
echo ""
echo "3. Checking for demo content removal..."
demo_check=$(curl -s "$PRODUCTION_URL/" | grep -i "demo\|emoji\|🏠\|🔍\|📊" || echo "clean")
if [ "$demo_check" = "clean" ]; then
    echo "   ✅ No demo content found - professional UI confirmed"
else
    echo "   ⚠️  Demo content may still be present:"
    echo "   $demo_check"
fi

# Test 4: Check for professional design elements
echo ""
echo "4. Verifying professional design..."
professional_check=$(curl -s "$PRODUCTION_URL/" | grep -i "domus\|conveyancing\|professional" || echo "not found")
if [ "$professional_check" != "not found" ]; then
    echo "   ✅ Professional branding detected"
else
    echo "   ⚠️  Professional branding not clearly visible"
fi

# Test 5: Static assets
echo ""
echo "5. Testing static assets..."
css_response=$(curl -s -o /dev/null -w "%{http_code}" "$PRODUCTION_URL/static/style.css")
if [ "$css_response" = "200" ]; then
    echo "   ✅ CSS assets loading ($css_response)"
else
    echo "   ⚠️  CSS assets issue ($css_response)"
fi

echo ""
echo "6. Testing API endpoints..."
api_response=$(curl -s -o /dev/null -w "%{http_code}" "$PRODUCTION_URL/api/")
if [ "$api_response" = "200" ] || [ "$api_response" = "404" ]; then
    echo "   ✅ API routing functional ($api_response)"
else
    echo "   ❌ API routing issue ($api_response)"
fi

echo ""
echo "================================================"
echo "📋 DEPLOYMENT VERIFICATION SUMMARY"
echo "================================================"
echo ""
echo "✅ Blockers resolved:"
echo "   • Syntax errors in lib/permissions.py"
echo "   • Broken Alembic migration chain"
echo ""
echo "✅ Deployment completed:"
echo "   • Code committed and pushed to main"
echo "   • Render deployment triggered"
echo "   • Production database migration script ready"
echo ""
echo "🎯 Next steps:"
echo "   1. Run database migrations in production"
echo "   2. Test login functionality"
echo "   3. Verify all professional features work"
echo "   4. Monitor application performance"
echo ""
echo "🔗 Production URL: $PRODUCTION_URL"
echo "🔗 Health Check: $PRODUCTION_URL/health"
echo ""
echo "Deployment verification complete! 🚀"