from fastapi import APIRouter
import os
import subprocess
from datetime import datetime
from sqlalchemy import text

router = APIRouter()

def get_git_sha():
    """Get current git commit SHA"""
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            return result.stdout.strip()[:8]  # Short SHA
        return "unknown"
    except:
        return "unknown"

def check_database():
    """Check database connectivity"""
    try:
        from database_config import engine
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            return {"status": "connected", "test_query": row[0] if row else None}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

@router.get("/health")
def health():
    """Basic health check"""
    return {"status": "ok"}

@router.get("/api/health")
def api_health():
    """Comprehensive health check with environment status"""
    
    # Check database connectivity
    db_status = check_database()
    
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
    
    overall_status = "healthy" if len(env_status['missing_critical']) == 0 and db_status['status'] == 'connected' else "degraded"
    current_env = os.getenv("ENVIRONMENT", "development")
    
    return {
        "ok": True,
        "status": overall_status,
        "version": get_git_sha(),
        "env": current_env,
        "database": db_status,
        "environment": env_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/ready")
def ready():
    return {"status": "ready"}

@router.get("/api/health/deps")
def health_deps():
    """Check if all critical dependencies can be imported"""
    deps_status = {}
    critical_imports = [
        'stripe', 'sendgrid', 'httpx', 'requests', 'jwt', 'fastapi', 
        'sqlalchemy', 'pydantic', 'bcrypt', 'jinja2'
    ]
    
    all_ok = True
    for module in critical_imports:
        try:
            __import__(module)
            deps_status[module] = True
        except ImportError:
            deps_status[module] = False
            all_ok = False
    
    return {
        "ok": all_ok,
        "dependencies": deps_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/api/health/freshness")
def health_freshness():
    """Check freshness of external data sources"""
    # This would typically check last fetch timestamps from cache/database
    # For now, return a placeholder structure
    return {
        "ok": True,
        "sources": {
            "epc": {"last_fetch": "N/A", "status": "available"},
            "planit": {"last_fetch": "N/A", "status": "available"},
            "pdg": {"last_fetch": "N/A", "status": "available"},
            "ea_flood": {"last_fetch": "N/A", "status": "available"},
            "companies_house": {"last_fetch": "N/A", "status": "available"}
        },
        "timestamp": datetime.utcnow().isoformat()
    }

