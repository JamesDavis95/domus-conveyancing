"""
Authentication and Authorization System
Handles user login, JWT tokens, RBAC, and quota enforcement
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from models import Users, Orgs, UsageCounters, UserRole, PlanType
import os

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Plan Quotas
PLAN_QUOTAS = {
    PlanType.CORE: {
        "projects": 1,
        "docs": 5,
        "api_calls": 100,
        "viability_runs": 1,
        "bng_calculations": 0,
        "transport_assessments": 0,
        "environment_assessments": 0,
        "submission_packs": 0,
        "appeals_queries": 0,
        "collaboration_invites": 0
    },
    PlanType.PROFESSIONAL: {
        "projects": 10,
        "docs": 50,
        "api_calls": 1000,
        "viability_runs": 25,
        "bng_calculations": 25,
        "transport_assessments": 25,
        "environment_assessments": 25,
        "submission_packs": 10,
        "appeals_queries": 100,
        "collaboration_invites": 50
    },
    PlanType.ENTERPRISE: {
        "projects": -1,  # Unlimited
        "docs": -1,     # Unlimited
        "api_calls": -1,  # Unlimited
        "viability_runs": -1,
        "bng_calculations": -1,
        "transport_assessments": -1,
        "environment_assessments": -1,
        "submission_packs": -1,
        "appeals_queries": -1,
        "collaboration_invites": -1
    }
}

# Role Permissions
ROLE_PERMISSIONS = {
    UserRole.DEVELOPER: [
        "dashboard", "projects", "planning-ai", "auto-docs", 
        "documents", "marketplace-demand", "analytics", "settings",
        "viability", "bng", "transport", "environment", "submission-pack",
        "objection-risk", "appeals", "collaboration"
    ],
    UserRole.CONSULTANT: [
        "dashboard", "projects", "planning-ai", "auto-docs", 
        "documents", "marketplace-demand", "analytics", "settings",
        "viability", "bng", "transport", "environment", "submission-pack",
        "objection-risk", "appeals", "collaboration"
    ],
    UserRole.LANDOWNER: [
        "dashboard", "marketplace-supply", "marketplace-demand", 
        "contracts", "analytics", "settings", "bng"
    ],
    UserRole.AUTHORITY: [
        "authority-portal", "submission-pack-view", "comments"
    ],
    UserRole.ADMIN: [
        "dashboard", "projects", "planning-ai", "auto-docs", 
        "documents", "marketplace-supply", "marketplace-demand", 
        "contracts", "analytics", "settings", "admin",
        "viability", "bng", "transport", "environment", "submission-pack",
        "objection-risk", "appeals", "collaboration", "analytics-lpa",
        "analytics-org", "org-insights"
    ],
    UserRole.SUPER_ADMIN: [
        "*"  # All permissions
    ]
}

security = HTTPBearer()

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(user_id: int, org_id: int, role: UserRole) -> str:
    """Create JWT access token"""
    payload = {
        "user_id": user_id,
        "org_id": org_id,
        "role": role.value,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(lambda: None)  # Will be injected properly
) -> dict:
    """Get current authenticated user from JWT token"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    payload = decode_token(credentials.credentials)
    
    # For now, return the payload. In production, validate user exists in DB
    return {
        "id": payload["user_id"],
        "org_id": payload["org_id"],
        "role": UserRole(payload["role"])
    }

def check_permission(user: dict, required_permission: str) -> bool:
    """Check if user has required permission"""
    user_role = user["role"]
    
    # Super admin has all permissions
    if user_role == UserRole.SUPER_ADMIN:
        return True
    
    # Check role-specific permissions
    permissions = ROLE_PERMISSIONS.get(user_role, [])
    return required_permission in permissions or "*" in permissions

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(user: dict = Depends(get_current_user)):
        if not check_permission(user, permission):
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied: {permission} permission required"
            )
        return user
    return decorator

def get_usage_for_month(db: Session, org_id: int, month: str) -> dict:
    """Get usage counters for specific month"""
    usage = db.query(UsageCounters).filter(
        UsageCounters.org_id == org_id,
        UsageCounters.month == month
    ).first()
    
    if not usage:
        # Create new usage record for the month
        usage = UsageCounters(
            org_id=org_id,
            month=month,
            projects_used=0,
            docs_used=0,
            api_calls_used=0
        )
        db.add(usage)
        db.commit()
        db.refresh(usage)
    
    return {
        "projects_used": usage.projects_used,
        "docs_used": usage.docs_used,
        "api_calls_used": usage.api_calls_used
    }

def check_quota(db: Session, org_id: int, quota_type: str, plan: PlanType) -> bool:
    """Check if organization is within quota limits"""
    current_month = datetime.utcnow().strftime("%Y-%m")
    usage = get_usage_for_month(db, org_id, current_month)
    
    # Get quota limit for plan
    quota_limit = PLAN_QUOTAS[plan][quota_type]
    
    # Unlimited quota (-1)
    if quota_limit == -1:
        return True
    
    # Check if under limit
    current_usage = usage[f"{quota_type}_used"]
    return current_usage < quota_limit

def increment_usage(db: Session, org_id: int, quota_type: str) -> None:
    """Increment usage counter"""
    current_month = datetime.utcnow().strftime("%Y-%m")
    
    usage = db.query(UsageCounters).filter(
        UsageCounters.org_id == org_id,
        UsageCounters.month == current_month
    ).first()
    
    if not usage:
        usage = UsageCounters(
            org_id=org_id,
            month=current_month
        )
        db.add(usage)
    
    # Increment the specific counter
    if quota_type == "projects":
        usage.projects_used += 1
    elif quota_type == "docs":
        usage.docs_used += 1
    elif quota_type == "api_calls":
        usage.api_calls_used += 1
    
    db.commit()

def require_quota(quota_type: str):
    """Decorator to check quota before allowing action"""
    def decorator(
        user: dict = Depends(get_current_user),
        db: Session = Depends(lambda: None)  # Will be injected properly
    ):
        # Get org plan (for now, assume Professional)
        plan = PlanType.PROFESSIONAL  # TODO: Get from DB
        
        if not check_quota(db, user["org_id"], quota_type, plan):
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "quota_exceeded",
                    "message": f"You have exceeded your {quota_type} quota for this month",
                    "upgrade_url": "/billing/upgrade"
                }
            )
        return user
    return decorator

def org_scoped_query(query, user: dict):
    """Apply organization scoping to database query"""
    return query.filter_by(org_id=user["org_id"])