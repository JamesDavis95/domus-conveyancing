# Explicitly export key symbols for import in app.py
__all__ = [
    'get_current_user',
    'QuotaEnforcement',
    'enforce_quota_middleware'
]
"""
Production Authentication System
Complete authentication, authorization, and billing enforcement
"""

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
import bcrypt
from models import get_db, User, Organization, Usage, Subscription

# Try to import backend auth - graceful fallback if not available
try:
    from backend_auth import UserRole, PlanType, PLAN_LIMITS
except ImportError as e:
    print(f"⚠️ Backend auth not available: {e}")
    # Define fallback enums
    import enum
    class UserRole(enum.Enum):
        DEVELOPER = "developer"
        CONSULTANT = "consultant"
        LANDOWNER = "landowner"
        ADMIN = "admin"
        SUPER_ADMIN = "super_admin"
    
    class PlanType(enum.Enum):
        CORE = "core"
        PROFESSIONAL = "professional"
        ENTERPRISE = "enterprise"
    
    PLAN_LIMITS = {
        PlanType.CORE: {"site_analyses_per_month": 10, "documents_per_month": 5},
        PlanType.PROFESSIONAL: {"site_analyses_per_month": 100, "documents_per_month": 50},
        PlanType.ENTERPRISE: {"site_analyses_per_month": -1, "documents_per_month": -1}
    }
from stripe_integration import StripeService

app = FastAPI()
security = HTTPBearer()

SECRET_KEY = "your-production-secret-key-change-this"  # Move to environment variable
ALGORITHM = "HS256"

class AuthService:
    @staticmethod
    async def authenticate_user(email: str, password: str, db: Session) -> dict:
        """Authenticate user and return user data"""
        user = db.query(User).filter(User.email == email, User.is_active == True).first()
        
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8')):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Get organization
        org = db.query(Organization).filter(Organization.id == user.org_id).first()
        
        return {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "org_id": user.org_id,
            "org_name": org.name if org else None,
            "plan_type": org.plan_type.value if org else PlanType.CORE.value
        }
    
    @staticmethod
    def create_access_token(user_data: dict) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(days=7)
        payload = {
            **user_data,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify JWT token and return user data"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """Get current authenticated user"""
    token = credentials.credentials
    user_data = AuthService.verify_token(token)
    
    # Verify user still exists and is active
    user = db.query(User).filter(
        User.id == user_data["user_id"],
        User.is_active == True
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user_data

class QuotaEnforcement:
    @staticmethod
    async def check_and_record_usage(
        resource_type: str,
        current_user: dict,
        db: Session
    ):
        """Check quota limits and record usage"""
        org = db.query(Organization).filter(Organization.id == current_user["org_id"]).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Get plan limits
        plan_limits = PLAN_LIMITS.get(org.plan_type, PLAN_LIMITS[PlanType.CORE])
        limit_key = f"{resource_type}_per_month"
        
        if limit_key not in plan_limits:
            raise HTTPException(status_code=400, detail=f"Unknown resource: {resource_type}")
        
        limit = plan_limits[limit_key]
        
        # Check if unlimited
        if limit == -1:
            # Still record usage for analytics
            usage_record = Usage(
                org_id=current_user["org_id"],
                user_id=current_user["user_id"],
                resource_type=resource_type,
                created_at=datetime.utcnow()
            )
            db.add(usage_record)
            db.commit()
            return
        
        # Count current month usage
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        
        current_usage = db.query(Usage).filter(
            Usage.org_id == current_user["org_id"],
            Usage.resource_type == resource_type,
            Usage.created_at >= month_start
        ).count()
        
        if current_usage >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": f"Monthly quota exceeded for {resource_type}",
                    "current_usage": current_usage,
                    "limit": limit,
                    "upgrade_required": True
                }
            )
        
        # Record successful usage
        usage_record = Usage(
            org_id=current_user["org_id"],
            user_id=current_user["user_id"],
            resource_type=resource_type,
            created_at=datetime.utcnow()
        )
        db.add(usage_record)
        db.commit()

# Authentication endpoints
@app.post("/api/auth/login")
async def login(request: Request, db: Session = Depends(get_db)):
    """User login endpoint"""
    body = await request.json()
    email = body.get("email")
    password = body.get("password")
    
    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password required"
        )
    
    try:
        user_data = await AuthService.authenticate_user(email, password, db)
        access_token = AuthService.create_access_token(user_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

@app.post("/api/auth/register")
async def register(request: Request, db: Session = Depends(get_db)):
    """User registration endpoint"""
    body = await request.json()
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == body["email"]).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    try:
        # Create organization
        org = Organization(
            name=body.get("company_name", f"{body['name']}'s Organization"),
            plan_type=PlanType.CORE,
            created_at=datetime.utcnow(),
            trial_end=datetime.utcnow() + timedelta(days=14)  # 14-day trial
        )
        db.add(org)
        db.commit()
        
        # Create user
        user = User(
            email=body["email"],
            name=body["name"],
            hashed_password=bcrypt.hashpw(body["password"].encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            role=UserRole.DEVELOPER,  # Default role
            org_id=org.id,
            created_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        
        # Create auth token
        user_data = {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "org_id": user.org_id,
            "org_name": org.name,
            "plan_type": org.plan_type.value
        }
        
        access_token = AuthService.create_access_token(user_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_data,
            "trial_end": org.trial_end.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return current_user

# Usage tracking endpoints
@app.get("/api/usage/current")
async def get_current_usage(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current usage statistics"""
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    
    # Get organization plan
    org = db.query(Organization).filter(Organization.id == current_user["org_id"]).first()
    plan_limits = PLAN_LIMITS.get(org.plan_type if org else PlanType.CORE, PLAN_LIMITS[PlanType.CORE])
    
    usage_stats = {}
    
    for resource_type in ["site_analyses", "documents", "api_calls"]:
        current_usage = db.query(Usage).filter(
            Usage.org_id == current_user["org_id"],
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
        "plan_type": org.plan_type.value if org else PlanType.CORE.value,
        "usage": usage_stats,
        "month_start": month_start.isoformat(),
        "trial_end": org.trial_end.isoformat() if org and org.trial_end else None
    }

# Middleware for quota enforcement
async def enforce_quota_middleware(request: Request, call_next):
    """Middleware to enforce quotas on protected endpoints"""
    
    # Map endpoints to resource types
    quota_endpoints = {
        "/api/planning-ai/analyze": "site_analyses",
        "/api/auto-docs/generate": "documents",
        "/api/property/lookup": "api_calls"
    }
    
    resource_type = quota_endpoints.get(request.url.path)
    
    if resource_type and request.method == "POST":
        # Extract user from auth header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                user_data = AuthService.verify_token(token)
                
                # Check quota before processing request
                db = next(get_db())
                try:
                    await QuotaEnforcement.check_and_record_usage(resource_type, user_data, db)
                finally:
                    db.close()
                    
            except HTTPException:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Quota exceeded. Please upgrade your plan."}
                )
    
    response = await call_next(request)
    return response