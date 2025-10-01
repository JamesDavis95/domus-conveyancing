"""
Backend Permission Enforcement System
Implements proper role-based access control and quota enforcement
"""

from functools import wraps
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
import bcrypt
from models import User, Organization, Usage
from db import get_db

# Security configuration
SECRET_KEY = "your-secret-key-change-in-production"  # TODO: Move to environment variable
ALGORITHM = "HS256"
security = HTTPBearer()

class UserRole:
    DEVELOPER = "developer"
    CONSULTANT = "consultant" 
    LANDOWNER = "landowner"
    ADMIN = "admin"

class PlanType:
    CORE = "core"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

# Plan limits configuration
PLAN_LIMITS = {
    PlanType.CORE: {
        "site_analyses_per_month": 10,
        "documents_per_month": 10,
        "api_calls_per_month": 1000,
        "users": 1,
        "marketplace_listings": 1
    },
    PlanType.PROFESSIONAL: {
        "site_analyses_per_month": -1,  # Unlimited
        "documents_per_month": -1,      # Unlimited
        "api_calls_per_month": 50000,
        "users": 5,
        "marketplace_listings": 10
    },
    PlanType.ENTERPRISE: {
        "site_analyses_per_month": -1,  # Unlimited
        "documents_per_month": -1,      # Unlimited
        "api_calls_per_month": 200000,
        "users": -1,                    # Unlimited
        "marketplace_listings": -1      # Unlimited
    }
}

def create_access_token(user_id: int, role: str, org_id: int) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(days=30)
    payload = {
        "user_id": user_id,
        "role": role,
        "org_id": org_id,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token"
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)  # You'll need to import this
) -> Dict[str, Any]:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return {
        "user_id": user.id,
        "role": user.role,
        "org_id": user.org_id,
        "email": user.email,
        "name": user.name
    }

def require_role(*allowed_roles: str):
    """Decorator to enforce role-based access control"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from dependency injection
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, dict) and "role" in value:
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if current_user["role"] not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def check_quota(resource_type: str):
    """Decorator to check and enforce usage quotas"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user and database from kwargs
            current_user = None
            db = None
            
            for key, value in kwargs.items():
                if isinstance(value, dict) and "org_id" in value:
                    current_user = value
                elif hasattr(value, 'query'):  # SQLAlchemy session
                    db = value
            
            if not current_user or not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Unable to verify quota"
                )
            
            # Get organization plan
            org = db.query(Organization).filter(Organization.id == current_user["org_id"]).first()
            if not org:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Organization not found"
                )
            
            plan_limits = PLAN_LIMITS.get(org.plan_type, PLAN_LIMITS[PlanType.CORE])
            limit_key = f"{resource_type}_per_month"
            
            if limit_key not in plan_limits:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown resource type: {resource_type}"
                )
            
            limit = plan_limits[limit_key]
            
            # Check if unlimited (-1)
            if limit == -1:
                return await func(*args, **kwargs)
            
            # Get current month usage
            now = datetime.utcnow()
            month_start = datetime(now.year, now.month, 1)
            
            usage = db.query(Usage).filter(
                Usage.org_id == current_user["org_id"],
                Usage.resource_type == resource_type,
                Usage.created_at >= month_start
            ).count()
            
            if usage >= limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Monthly quota exceeded for {resource_type}. Used: {usage}/{limit}. Upgrade your plan for higher limits."
                )
            
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Record usage
            usage_record = Usage(
                org_id=current_user["org_id"],
                user_id=current_user["user_id"],
                resource_type=resource_type,
                created_at=datetime.utcnow()
            )
            db.add(usage_record)
            db.commit()
            
            return result
        return wrapper
    return decorator

async def get_user_usage(user_id: int, org_id: int, db: Session) -> Dict[str, Any]:
    """Get current usage statistics for user/organization"""
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    
    # Get organization plan
    org = db.query(Organization).filter(Organization.id == org_id).first()
    plan_limits = PLAN_LIMITS.get(org.plan_type if org else PlanType.CORE, PLAN_LIMITS[PlanType.CORE])
    
    usage_stats = {}
    
    for resource_type in ["site_analyses", "documents", "api_calls"]:
        current_usage = db.query(Usage).filter(
            Usage.org_id == org_id,
            Usage.resource_type == resource_type,
            Usage.created_at >= month_start
        ).count()
        
        limit = plan_limits.get(f"{resource_type}_per_month", 0)
        
        usage_stats[resource_type] = {
            "current": current_usage,
            "limit": limit if limit != -1 else "unlimited",
            "percentage": (current_usage / limit * 100) if limit > 0 else 0
        }
    
    return {
        "plan_type": org.plan_type if org else PlanType.CORE,
        "usage": usage_stats,
        "month_start": month_start.isoformat()
    }

# Password hashing utilities
def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Middleware for automatic quota checking
class QuotaMiddleware:
    """Middleware to automatically check quotas on API endpoints"""
    
    QUOTA_ENDPOINTS = {
        "/api/planning-ai/analyze": "site_analyses",
        "/api/auto-docs/generate": "documents",
        "/api/property/lookup": "api_calls"
    }
    
    async def __call__(self, request, call_next):
        # Check if endpoint requires quota checking
        path = request.url.path
        resource_type = self.QUOTA_ENDPOINTS.get(path)
        
        if resource_type:
            # Add quota check to request context
            request.state.quota_check = resource_type
        
        response = await call_next(request)
        return response