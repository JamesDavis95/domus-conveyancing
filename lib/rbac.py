"""
RBAC Middleware - Role-Based Access Control for FastAPI
Enforces feature permissions at the route level
"""
from typing import Optional, List
from fastapi import HTTPException, Depends, Request
from functools import wraps
import jwt
from sqlalchemy.orm import Session

from lib.permissions import UserContext, Role, Feature, has_feature_access
from models import get_db, Users, Orgs
from auth_system import get_current_user

class RBACMiddleware:
    """Middleware for enforcing role-based access control"""
    
    @staticmethod
    def require_feature(required_feature: Feature):
        """Decorator to require specific feature access"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract user from dependencies
                user = None
                for arg in args:
                    if isinstance(arg, dict) and "id" in arg and "role" in arg:
                        user = arg
                        break
                
                if not user:
                    raise HTTPException(status_code=401, detail="Authentication required")
                
                # Convert string role to Role enum
                try:
                    user_role = Role(user["role"])
                except ValueError:
                    raise HTTPException(status_code=403, detail="Invalid user role")
                
                # Check feature access
                if not has_feature_access(user_role, required_feature):
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Access denied: {required_feature.value} feature not available for role {user_role.value}"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def require_role(required_roles: List[Role]):
        """Decorator to require specific role(s)"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract user from dependencies
                user = None
                for arg in args:
                    if isinstance(arg, dict) and "id" in arg and "role" in arg:
                        user = arg
                        break
                
                if not user:
                    raise HTTPException(status_code=401, detail="Authentication required")
                
                # Convert string role to Role enum
                try:
                    user_role = Role(user["role"])
                except ValueError:
                    raise HTTPException(status_code=403, detail="Invalid user role")
                
                # Check role access
                if user_role not in required_roles:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Access denied: requires one of {[r.value for r in required_roles]}, got {user_role.value}"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator

# Convenience functions for common permission checks
def require_projects_access():
    """Require access to projects feature"""
    return RBACMiddleware.require_feature(Feature.PROJECTS)

def require_planning_ai_access():
    """Require access to planning AI feature"""
    return RBACMiddleware.require_feature(Feature.PLANNING_AI)

def require_autodocs_access():
    """Require access to auto-docs feature"""
    return RBACMiddleware.require_feature(Feature.AUTODOCS)

def require_documents_access():
    """Require access to documents feature"""
    return RBACMiddleware.require_feature(Feature.DOCUMENTS)

def require_marketplace_supply_access():
    """Require access to marketplace supply feature (landowners only)"""
    return RBACMiddleware.require_feature(Feature.MKT_SUPPLY)

def require_marketplace_demand_access():
    """Require access to marketplace demand feature (developers/consultants)"""
    return RBACMiddleware.require_feature(Feature.MKT_DEMAND)

def require_contracts_access():
    """Require access to contracts feature"""
    return RBACMiddleware.require_feature(Feature.CONTRACTS)

def require_analytics_access():
    """Require access to analytics feature"""
    return RBACMiddleware.require_feature(Feature.ANALYTICS)

def require_admin_access():
    """Require admin access"""
    return RBACMiddleware.require_feature(Feature.ADMIN)

def require_authority_access():
    """Require authority portal access"""
    return RBACMiddleware.require_feature(Feature.AUTH_PORTAL)

# Role-specific decorators
def require_dev_or_consultant():
    """Require developer or consultant role"""
    return RBACMiddleware.require_role([Role.DEV, Role.CON])

def require_landowner():
    """Require landowner role"""
    return RBACMiddleware.require_role([Role.OWN])

def require_admin():
    """Require admin role"""
    return RBACMiddleware.require_role([Role.ADM])

def require_authority():
    """Require authority role"""
    return RBACMiddleware.require_role([Role.AUTH])

# Enhanced permission check with database context
async def check_feature_permission(
    user: dict = Depends(get_current_user),
    required_feature: Feature = None,
    db: Session = Depends(get_db)
) -> UserContext:
    """
    Enhanced permission check that returns full user context
    Use this for endpoints that need detailed user information
    """
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get user details from database
    db_user = db.query(Users).filter(Users.id == user["id"]).first()
    if not db_user or not db_user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    # Get organization details
    org = db.query(Orgs).filter(Orgs.id == user["org_id"]).first()
    if not org:
        raise HTTPException(status_code=401, detail="Organization not found")
    
    # Convert to enums
    try:
        user_role = Role(db_user.role.value)
        plan_type = org.plan  # Assuming this is already enum
    except (ValueError, AttributeError):
        raise HTTPException(status_code=403, detail="Invalid user role or plan")
    
    # Check feature permission if required
    if required_feature and not has_feature_access(user_role, required_feature):
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: {required_feature.value} feature not available for role {user_role.value}"
        )
    
    return UserContext(
        user_id=db_user.id,
        org_id=org.id,
        role=user_role,
        plan=plan_type,
        is_active=db_user.is_active
    )

# Org-scoped query helper
def org_scoped_query(query, user_context: UserContext):
    """
    Apply organization scoping to a SQLAlchemy query
    Ensures users can only access their organization's data
    """
    return query.filter_by(org_id=user_context.org_id)

def org_scoped_query_simple(query, user: dict):
    """
    Simple org scoping using user dict (for backward compatibility)
    """
    return query.filter_by(org_id=user["org_id"])