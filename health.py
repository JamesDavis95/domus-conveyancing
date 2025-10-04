from fastapi import APIRouter
import os
from datetime import datetime

router = APIRouter()

@router.get("/health")
def health():
    """Basic health check"""
    return {"status": "ok"}

@router.get("/api/health")
def api_health():
    """Comprehensive health check with environment status"""
    
    # Required server-side environment variables
    required_server_vars = [
        'STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET', 
        'STRIPE_PRICE_DEVELOPER', 'STRIPE_PRICE_DEVPRO', 'STRIPE_PRICE_CONSULTANT', 
        'STRIPE_PRICE_ENTERPRISE', 'STRIPE_PRICE_AI_CREDITS', 'STRIPE_PRICE_DOC_CREDITS', 
        'STRIPE_PRICE_BUNDLE_CREDITS',
        'OPENAI_API_KEY', 'SENDGRID_API_KEY', 'EPC_AUTH_BASIC', 'CH_API_KEY', 
        'OS_API_KEY', 'RECAPTCHA_SECRET_KEY',
        'EA_FLOOD_BASE_URL', 'PLANIT_API_BASE_URL', 'PDG_API_BASE_URL'
    ]
    
    # Frontend-safe environment variables
    frontend_vars = [
        'STRIPE_PUBLISHABLE_KEY', 'MAPBOX_ACCESS_TOKEN', 'RECAPTCHA_SITE_KEY'
    ]
    
    env_status = {
        'server_variables': {},
        'frontend_variables': {},
        'missing_critical': [],
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Check server variables (names only, no values)
    for var in required_server_vars:
        value = os.getenv(var)
        is_set = bool(value and len(value.strip()) > 0)
        env_status['server_variables'][var] = is_set
        if not is_set:
            env_status['missing_critical'].append(var)
    
    # Check frontend variables (names only, no values)
    for var in frontend_vars:
        value = os.getenv(var)
        is_set = bool(value and len(value.strip()) > 0)
        env_status['frontend_variables'][var] = is_set
    
    overall_status = "healthy" if len(env_status['missing_critical']) == 0 else "degraded"
    
    return {
        "status": overall_status,
        "environment": env_status,
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/ready")
def ready():
    return {"status": "ready"}

