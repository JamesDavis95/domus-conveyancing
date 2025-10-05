"""
Role-Based Access Control (RBAC) system for Domus
Server-side permissions enforcement with org scoping
"""

from dataclasses import dataclass
from typing import Tuple, Dict, Set, Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database_config import get_db
from models import User, Organization, Membership
import jwt
import os

# ----- Roles & permissions -----

ROLES: Tuple[str, ...] = (
    "Owner",
    "Admin", 
    "Manager",
    "Staff",
    "BillingOnly",
    "ReadOnly",
    "Client",
)

# Canonical permission names
PERMISSIONS: Tuple[str, ...] = (
    "org:read", "org:write",
    "users:read", "users:invite", "users:role:set", 
    "roles:read", "roles:write",
    "cases:read", "cases:write", "cases:assign",
    "documents:read", "documents:write",
    "billing:read", "billing:manage",
    "enterprise:read",
    "audit:read",
)

ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "Owner": set(PERMISSIONS),
    "Admin": set(PERMISSIONS) - {"org:write"},  # if you want Owner-only org ownership transfer
    "Manager": {
        "org:read",
        "users:read", 
        "cases:read", "cases:write", "cases:assign",
        "documents:read", "documents:write",
        "enterprise:read",
        "audit:read",
    },
    "Staff": {
        "org:read",
        "cases:read", "cases:write",
        "documents:read", "documents:write",
        # NOTE: runtime scoping limits to assigned cases
    },
    "BillingOnly": {"billing:read", "billing:manage"},
    "ReadOnly": {"org:read", "cases:read", "documents:read", "enterprise:read", "audit:read"},
    "Client": {"cases:read", "documents:read"},  # runtime scoping to own cases
}

@dataclass
class AuthContext:
    request: Request
    user: object
    org: object 
    membership: object

def get_current_user_from_token(token: str, db: Session) -> Optional[User]:
    """Extract user from JWT token"""
    try:
        # Replace with your JWT secret from environment
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
    """Dependency that returns (user, org, membership) or raises 401"""
    def _dep(request: Request, db: Session = Depends(get_db)):
        # Simplified auth for now - implement full auth logic here
        # This is a placeholder that should be implemented properly
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication not yet implemented"
        )
    return _dep

def require_permission(perm: str):
    """FastAPI dependency to require specific permission"""
    def _dep(ctx=Depends(require_auth())):
        user, org, membership = ctx
        role = getattr(membership, "role", None)
        perms = ROLE_PERMISSIONS.get(role, set())
        if perm not in perms:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return (user, org, membership)
    return _dep
