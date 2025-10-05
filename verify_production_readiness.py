#!/usr/bin/env python3
"""
Deployment Verification Script for Domus Production
Checks all environment variables and production readiness
"""

import os
import sys
from datetime import datetime

def check_env_vars():
    """Check all required environment variables"""
    print("🔍 ENVIRONMENT VARIABLES CHECK")
    print("=" * 50)
    
    # Required server-side environment variables for full production UI
    required_server_vars = {
        'STRIPE_SECRET_KEY': 'Stripe API secret key',
        'STRIPE_WEBHOOK_SECRET': 'Stripe webhook secret',
        'STRIPE_PRICE_DEVELOPER': 'Stripe Developer plan price ID',
        'STRIPE_PRICE_DEVPRO': 'Stripe DevPro plan price ID', 
        'STRIPE_PRICE_CONSULTANT': 'Stripe Consultant plan price ID',
        'STRIPE_PRICE_ENTERPRISE': 'Stripe Enterprise plan price ID',
        'STRIPE_PRICE_AI_CREDITS': 'Stripe AI Credits price ID',
        'STRIPE_PRICE_DOC_CREDITS': 'Stripe Doc Credits price ID',
        'STRIPE_PRICE_BUNDLE_CREDITS': 'Stripe Bundle Credits price ID',
        'OPENAI_API_KEY': 'OpenAI API key for AI features',
        'SENDGRID_API_KEY': 'SendGrid API key for emails',
        'EPC_AUTH_BASIC': 'EPC service Basic auth header',
        'CH_API_KEY': 'Companies House API key',
        'OS_API_KEY': 'Ordnance Survey API key',
        'RECAPTCHA_SECRET_KEY': 'reCAPTCHA secret key',
        'EA_FLOOD_BASE_URL': 'Environment Agency Flood API base URL',
        'PLANIT_API_BASE_URL': 'PlanIt API base URL',
        'PDG_API_BASE_URL': 'PDG API base URL'
    }
    
    # Frontend-safe environment variables
    frontend_vars = {
        'STRIPE_PUBLISHABLE_KEY': 'Stripe publishable key',
        'MAPBOX_ACCESS_TOKEN': 'Mapbox access token for maps',
        'RECAPTCHA_SITE_KEY': 'reCAPTCHA site key'
    }
    
    # Production control variables
    control_vars = {
        'ENVIRONMENT': 'Should be "production"',
        'DEMO_MODE': 'Should be "false"',
        'DATABASE_URL': 'PostgreSQL connection string',
        'STATIC_BUILD_ID': 'Cache-busting build ID'
    }
    
    missing_critical = []
    present_count = 0
    total_count = len(required_server_vars) + len(frontend_vars)
    
    print("\n📋 SERVER VARIABLES (Critical for Production UI)")
    for var, desc in required_server_vars.items():
        value = os.getenv(var)
        status = "✅ SET" if value else "❌ MISSING"
        print(f"  {var}: {status} - {desc}")
        if value:
            present_count += 1
        else:
            missing_critical.append(var)
    
    print("\n📋 FRONTEND VARIABLES (Required for Client Features)")
    for var, desc in frontend_vars.items():
        value = os.getenv(var)
        status = "✅ SET" if value else "❌ MISSING"
        print(f"  {var}: {status} - {desc}")
        if value:
            present_count += 1
        else:
            missing_critical.append(var)
    
    print("\n📋 CONTROL VARIABLES")
    for var, desc in control_vars.items():
        value = os.getenv(var)
        status = f"✅ {value}" if value else "❌ MISSING"
        print(f"  {var}: {status} - {desc}")
    
    print(f"\n📊 SUMMARY: {present_count}/{total_count} critical variables set")
    
    if missing_critical:
        print(f"\n❌ MISSING CRITICAL VARIABLES ({len(missing_critical)}):")
        for var in missing_critical:
            print(f"  - {var}")
        print("\n💡 These variables gate the production UI features!")
        return False
    else:
        print("\n✅ ALL CRITICAL VARIABLES PRESENT")
        return True

def check_imports():
    """Test critical imports"""
    print("\n🔍 IMPORT VERIFICATION")
    print("=" * 50)
    
    critical_imports = [
        ('lib.permissions', 'has_feature_access'),
        ('lib.permissions', 'check_access'), 
        ('lib.permissions', 'UserContext'),
        ('database_config', 'engine'),
        ('database_config', 'SessionLocal'),
        ('app', 'app')
    ]
    
    all_good = True
    for module, item in critical_imports:
        try:
            mod = __import__(module, fromlist=[item])
            getattr(mod, item)
            print(f"  ✅ {module}.{item}")
        except Exception as e:
            print(f"  ❌ {module}.{item} - {e}")
            all_good = False
    
    return all_good

def check_database():
    """Test database connectivity if DATABASE_URL is set"""
    print("\n🔍 DATABASE CONNECTION")
    print("=" * 50)
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("  ❌ DATABASE_URL not set")
        return False
    
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.engine.url import make_url
        
        # Parse URL
        url = make_url(db_url)
        print(f"  📊 Database: {url.drivername}://{url.host}/{url.database}")
        
        # Normalize for psycopg
        if url.drivername in ("postgres", "postgresql"):
            if "+psycopg" not in str(url):
                url = url.set(drivername="postgresql+psycopg")
                print(f"  🔄 Normalized to: {url.drivername}")
        
        # Test connection
        engine = create_engine(str(url))
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"  ✅ Connection successful, test query: {row[0]}")
            return True
            
    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
        return False

def check_production_readiness():
    """Overall production readiness check"""
    print("\n🔍 PRODUCTION READINESS")
    print("=" * 50)
    
    env = os.getenv("ENVIRONMENT", "development")
    demo_mode = os.getenv("DEMO_MODE", "true").lower()
    
    print(f"  Environment: {env}")
    print(f"  Demo Mode: {demo_mode}")
    
    ready = True
    
    if env != "production":
        print("  ⚠️  ENVIRONMENT should be 'production'")
        ready = False
    else:
        print("  ✅ Environment is production")
    
    if demo_mode != "false":
        print("  ⚠️  DEMO_MODE should be 'false'")
        ready = False
    else:
        print("  ✅ Demo mode disabled")
    
    return ready

def main():
    """Run all verification checks"""
    print("🚀 DOMUS PRODUCTION DEPLOYMENT VERIFICATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    
    results = {
        'env_vars': check_env_vars(),
        'imports': check_imports(),
        'database': check_database(),
        'production': check_production_readiness()
    }
    
    print("\n🎯 FINAL RESULTS")
    print("=" * 50)
    
    all_passed = True
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {check.upper()}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL CHECKS PASSED - READY FOR PRODUCTION!")
        print("\n📋 Next Steps:")
        print("  1. Deploy to Render with all environment variables")
        print("  2. Verify /api/health shows 'healthy' status")
        print("  3. Check homepage shows full production design")
        print("  4. Test billing/plan features load real prices")
        return 0
    else:
        print("\n💥 SOME CHECKS FAILED - FIX BEFORE DEPLOYMENT!")
        print("\n📋 Required Actions:")
        if not results['env_vars']:
            print("  1. Set missing environment variables in Render")
        if not results['imports']:
            print("  2. Fix import errors in codebase")
        if not results['database']:
            print("  3. Verify DATABASE_URL and connection")
        if not results['production']:
            print("  4. Set ENVIRONMENT=production and DEMO_MODE=false")
        return 1

if __name__ == "__main__":
    sys.exit(main())