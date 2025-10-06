"""
Role-Based Access Control (RBAC) system for Domus AI Platform
"""

from dataclasses import dataclass
from typing import Tuple, Dict, Set, Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database_config import get_db
from models import User, Organization, Membership
import jwt
import os

ROLES = (
    "Owner", "Admin", "Manager", "Staff", 
    "BillingOnly", "ReadOnly", "Client", "LA"
)

PERMISSIONS = (
    "sites:create", "sites:read", "sites:update", "sites:delete",
    "ai:analyze", "ai:suggest", "ai:chat",
    "docs:generate", "docs:read",
    "bundle:create", "calc:run",
    "billing:read", "billing:manage",
    "users:invite", "users:assign_roles",
    "org:read", "org:write", "audit:read", "la:dashboard:read"
)

ROLE_PERMISSIONS = {
    "Owner": set(PERMISSIONS),
    "Admin": set(PERMISSIONS) - {"org:write"},
    "Manager": {
        "sites:create", "sites:read", "sites:update", "sites:delete",
        "ai:analyze", "ai:suggest", "ai:chat",
        "docs:generate", "docs:read",
        "bundle:create", "calc:run", "audit:read"
    },
    "Staff": {
        "sites:create", "sites:read", "sites:update",
        "ai:analyze", "ai:suggest",
        "docs:generate", "docs:read", "calc:run"
    },
    "BillingOnly": {"billing:read", "billing:manage"},
    "ReadOnly": {"sites:read", "docs:read", "audit:read"},
    "Client": {"sites:read", "docs:read"},
    "LA": {"la:dashboard:read"}
}

@dataclass
class AuthContext:
    """Authentication context for the current request"""
    request: Request
    user: User
    org: Organization
    membership: Membership

def get_current_user_from_token(token: str, db: Session) -> Optional[User]:
    """Extract user from JWT token"""
    try:
        secret = os.getenv("JWT_SECRET", "your-secret-key")
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        user_id = payload.get("sub")
        
        if user_id is None:
            return None
            
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        return user
    except jwt.PyJWTError:
        return None

def require_auth():
    """Dependency that returns AuthContext or raises 401"""
    def _dep(request: Request, db: Session = Depends(get_db)) -> AuthContext:
        # For now, create a mock context for development
        # TODO: Implement proper JWT authentication
        from models import User, Organization, Membership
        
        # Mock user for development
        mock_user = User(id=1, email="demo@domus.ai", is_active=True)
        mock_org = Organization(id=1, name="Demo Organization")
        mock_membership = Membership(user_id=1, organization_id=1, role="Manager", is_active=True)
        
        return AuthContext(
            request=request,
            user=mock_user,
            org=mock_org,
            membership=mock_membership
        )
    
    return _dep

def require_permission(perm: str):
    """FastAPI dependency to require specific permission"""
    def _dep(ctx: AuthContext = Depends(require_auth())):
        user_role = ctx.membership.role
        
        if user_role not in ROLE_PERMISSIONS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Invalid role: {user_role}"
            )
        
        user_permissions = ROLE_PERMISSIONS[user_role]
        
        if perm not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {perm}"
            )
        
        return ctx
    
    return _dep

def has_permission(user_role: str, permission: str) -> bool:
    """Check if a role has a specific permission"""
    if user_role not in ROLE_PERMISSIONS:
        return False
    return permission in ROLE_PERMISSIONS[user_role]

def get_user_permissions(user_role: str) -> Set[str]:
    """Get all permissions for a role"""
    return ROLE_PERMISSIONS.get(user_role, set())
