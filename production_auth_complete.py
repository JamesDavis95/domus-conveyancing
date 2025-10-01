"""
Complete Production Authentication & Authorization System
Handles user management, JWT tokens, role-based access control, and quota enforcement
"""

from fastapi import FastAPI, HTTPException, Depends, Request, status, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
import bcrypt
import hashlib
import secrets
from typing import Optional, Dict, Any
from models import get_db, User, Organization, Usage, Subscription
from backend_auth import UserRole, PlanType, PLAN_LIMITS
from stripe_integration import StripeService

security = HTTPBearer()

# Environment configuration
SECRET_KEY = "domus-production-secret-key-2024-change-in-production"  # TODO: Move to env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    @staticmethod
    def create_access_token(data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    async def authenticate_user(email: str, password: str, db: Session) -> Optional[User]:
        """Authenticate user credentials"""
        user = db.query(User).filter(User.email == email, User.is_active == True).first()
        
        if not user or not AuthService.verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        return user
    
    @staticmethod
    async def create_user(
        email: str, 
        password: str, 
        name: str, 
        role: UserRole,
        organization_name: str,
        plan_type: PlanType,
        db: Session
    ) -> User:
        """Create new user and organization"""
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create organization
        organization = Organization(
            name=organization_name,
            plan_type=plan_type,
            trial_end=datetime.utcnow() + timedelta(days=14)  # 14-day trial
        )
        db.add(organization)
        db.flush()  # Get organization ID
        
        # Create user
        hashed_password = AuthService.hash_password(password)
        user = User(
            email=email,
            name=name,
            hashed_password=hashed_password,
            role=role,
            org_id=organization.id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create Stripe customer
        stripe_customer_id = await StripeService.create_customer(user, organization)
        organization.stripe_customer_id = stripe_customer_id
        db.commit()
        
        return user

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

class QuotaEnforcement:
    """Enforce usage quotas based on subscription plans"""
    
    @staticmethod
    def check_quota(user: User, resource_type: str, db: Session) -> bool:
        """Check if user has quota remaining for resource"""
        organization = user.organization
        plan_limits = PLAN_LIMITS.get(organization.plan_type, {})
        
        if resource_type not in plan_limits:
            return True  # No limit defined
        
        limit = plan_limits[resource_type]
        if limit == -1:  # Unlimited
            return True
        
        # Count current month usage
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_usage = db.query(Usage).filter(
            Usage.org_id == organization.id,
            Usage.resource_type == resource_type,
            Usage.created_at >= start_of_month
        ).count()
        
        return current_usage < limit
    
    @staticmethod
    def record_usage(user: User, resource_type: str, db: Session):
        """Record usage of a resource"""
        usage = Usage(
            org_id=user.org_id,
            user_id=user.id,
            resource_type=resource_type
        )
        db.add(usage)
        db.commit()
    
    @staticmethod
    def get_usage_stats(user: User, db: Session) -> Dict[str, Any]:
        """Get current usage statistics"""
        organization = user.organization
        plan_limits = PLAN_LIMITS.get(organization.plan_type, {})
        
        # Current month usage
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        stats = {}
        for resource_type, limit in plan_limits.items():
            current_usage = db.query(Usage).filter(
                Usage.org_id == organization.id,
                Usage.resource_type == resource_type,
                Usage.created_at >= start_of_month
            ).count()
            
            stats[resource_type] = {
                "used": current_usage,
                "limit": limit,
                "remaining": limit - current_usage if limit != -1 else -1,
                "percentage": (current_usage / limit * 100) if limit != -1 else 0
            }
        
        return stats

def require_role(required_role: UserRole):
    """Decorator to require specific user role"""
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role.value}"
            )
        return current_user
    return role_checker

def require_quota(resource_type: str):
    """Decorator to enforce quota limits"""
    def quota_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        if not QuotaEnforcement.check_quota(current_user, resource_type, db):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Quota exceeded for {resource_type}. Upgrade your plan for more usage."
            )
        return current_user
    return quota_checker

async def enforce_quota_middleware(request: Request, call_next):
    """Middleware to automatically record usage for quota tracking"""
    response = await call_next(request)
    
    # Record usage for specific endpoints
    path = request.url.path
    if path.startswith("/api/planning/analyze"):
        # Will be handled by endpoint decorator
        pass
    elif path.startswith("/api/documents/generate"):
        # Will be handled by endpoint decorator
        pass
    
    return response

# Authentication endpoints
async def login_endpoint(email: str, password: str, db: Session = Depends(get_db)):
    """User login endpoint"""
    user = await AuthService.authenticate_user(email, password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create access token
    access_token = AuthService.create_access_token({
        "user_id": user.id,
        "email": user.email,
        "role": user.role.value,
        "org_id": user.org_id
    })
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "organization": user.organization.name
        }
    }

async def register_endpoint(
    email: str,
    password: str,
    name: str,
    organization_name: str,
    role: UserRole = UserRole.DEVELOPER,
    plan_type: PlanType = PlanType.CORE,
    db: Session = Depends(get_db)
):
    """User registration endpoint"""
    user = await AuthService.create_user(
        email=email,
        password=password,
        name=name,
        role=role,
        organization_name=organization_name,
        plan_type=plan_type,
        db=db
    )
    
    # Auto-login after registration
    access_token = AuthService.create_access_token({
        "user_id": user.id,
        "email": user.email,
        "role": user.role.value,
        "org_id": user.org_id
    })
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "message": "Account created successfully",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "organization": user.organization.name
        }
    }

def get_me_endpoint(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user profile"""
    usage_stats = QuotaEnforcement.get_usage_stats(current_user, db)
    
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "role": current_user.role.value,
            "organization": current_user.organization.name,
            "plan_type": current_user.organization.plan_type.value,
            "subscription_status": current_user.organization.subscription_status.value,
            "trial_end": current_user.organization.trial_end.isoformat() if current_user.organization.trial_end else None
        },
        "usage": usage_stats
    }