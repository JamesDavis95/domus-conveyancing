#!/usr/bin/env python3
"""
Final production readiness check - validates all code fixes are in place
"""

import os
import sys

def test_imports():
    """Test all critical imports work"""
    print("🔍 Testing critical imports...")
    
    try:
        # Test the fixed imports
        from lib.permissions import has_feature_access, check_access, UserContext
        print("✅ lib.permissions imports work")
        
        # Test the functions work
        ctx = UserContext(1, 1, 'admin')
        assert has_feature_access(ctx, 'test') == True
        assert check_access(ctx, 'test') == True
        print("✅ Permission functions work correctly")
        
        # Test app imports
        from app import app
        route_count = len([r for r in app.routes if hasattr(r, 'path')])
        print(f"✅ App imports with {route_count} routes")
        
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_alembic_config():
    """Test Alembic configuration is correct"""
    print("\n🔍 Testing Alembic configuration...")
    
    try:
        # Check alembic.ini has no hard-coded URL
        with open('alembic.ini', 'r') as f:
            content = f.read()
            if 'sqlalchemy.url = sqlite' in content:
                print("❌ alembic.ini still has hard-coded SQLite URL")
                return False
            print("✅ alembic.ini has no hard-coded database URL")
        
        # Test env.py can handle DATABASE_URL normalization
        with open('alembic/env.py', 'r') as f:
            env_content = f.read()
            if 'postgresql+psycopg' in env_content and 'DATABASE_URL' in env_content:
                print("✅ alembic/env.py has DATABASE_URL normalization")
            else:
                print("❌ alembic/env.py missing DATABASE_URL normalization")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Alembic config test failed: {e}")
        return False

def test_database_config():
    """Test database configuration"""
    print("\n🔍 Testing database configuration...")
    
    try:
        with open('database_config.py', 'r') as f:
            content = f.read()
            
        # Check for proper psycopg handling
        if 'postgresql+psycopg' in content:
            print("✅ database_config.py has psycopg driver setup")
        else:
            print("❌ database_config.py missing psycopg driver setup")
            return False
            
        # Check for SSL configuration
        if 'sslmode' in content:
            print("✅ database_config.py has SSL configuration")
        else:
            print("❌ database_config.py missing SSL configuration")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Database config test failed: {e}")
        return False

def main():
    """Run all production readiness tests"""
    print("🚀 FINAL PRODUCTION READINESS CHECK")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Alembic Config", test_alembic_config), 
        ("Database Config", test_database_config)
    ]
    
    all_passed = True
    for name, test_func in tests:
        if not test_func():
            all_passed = False
    
    print(f"\n🎯 FINAL RESULT")
    print("=" * 30)
    
    if all_passed:
        print("✅ ALL CODE FIXES VERIFIED - READY FOR DEPLOYMENT!")
        print("\n📋 Next: Set environment variables in Render using DEPLOYMENT_GUIDE.md")
        return 0
    else:
        print("❌ SOME CODE ISSUES REMAIN - FIX BEFORE DEPLOYMENT!")
        return 1

if __name__ == "__main__":
    sys.exit(main())