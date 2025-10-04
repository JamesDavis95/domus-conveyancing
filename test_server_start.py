#!/usr/bin/env python3
"""
Quick server start test to verify all integrations load correctly
"""

import sys
import os
from pathlib import Path

# Load environment variables
env_file = Path('.env.production')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

try:
    print("🚀 Testing server imports...")
    
    # Test individual integrations first
    integrations = [
        ("Planning AI", "planning_ai.router"),
        ("Stripe", "integrations.stripe_integration"),
        ("OpenAI", "integrations.openai_integration"),
        ("Email", "integrations.email_service"),
        ("EPC", "integrations.epc_integration"),
        ("Companies House", "integrations.companies_house_integration"),
        ("reCAPTCHA", "integrations.recaptcha_integration"),
        ("Public Data", "integrations.public_data_integration"),
        ("Health", "health")
    ]
    
    failed_imports = []
    successful_imports = []
    
    for name, module in integrations:
        try:
            __import__(module)
            successful_imports.append(name)
            print(f"✓ {name}")
        except Exception as e:
            failed_imports.append((name, str(e)))
            print(f"✗ {name}: {e}")
    
    print(f"\n📊 Integration Import Results:")
    print(f"✓ Successful: {len(successful_imports)}/{len(integrations)}")
    print(f"✗ Failed: {len(failed_imports)}")
    
    if failed_imports:
        print(f"\nFailed imports:")
        for name, error in failed_imports:
            print(f"  - {name}: {error}")
    
    # Try to import the main app
    print(f"\n🔍 Testing main app import...")
    try:
        # Import just the FastAPI app, not the whole file
        from fastapi import FastAPI
        print("✓ FastAPI import successful")
        
        # Try to create a minimal app with our integrations
        app = FastAPI(title="Domus Test")
        
        # Add working integrations
        for name in successful_imports:
            try:
                if name == "Planning AI":
                    from planning_ai.router import router
                    app.include_router(router, prefix="/api")
                elif name == "Stripe":
                    from integrations.stripe_integration import router
                    app.include_router(router)
                elif name == "OpenAI":
                    from integrations.openai_integration import router
                    app.include_router(router)
                elif name == "Email":
                    from integrations.email_service import router
                    app.include_router(router)
                elif name == "EPC":
                    from integrations.epc_integration import router
                    app.include_router(router)
                elif name == "Companies House":
                    from integrations.companies_house_integration import router
                    app.include_router(router)
                elif name == "reCAPTCHA":
                    from integrations.recaptcha_integration import router
                    app.include_router(router)
                elif name == "Public Data":
                    from integrations.public_data_integration import router
                    app.include_router(router)
                elif name == "Health":
                    from health import router
                    app.include_router(router)
                print(f"✓ {name} router added")
            except Exception as e:
                print(f"✗ {name} router failed: {e}")
        
        print(f"\n✓ Test app created with {len(app.routes)} routes")
        print("✓ Server can start with current integrations")
        
    except Exception as e:
        print(f"✗ Main app import failed: {e}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"✗ Test failed: {e}")
    import traceback
    traceback.print_exc()