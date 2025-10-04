"""
Server-Side RBAC and Quota Enforcement Middleware
Enforces permissions and usage limits on all API endpoints
"""

from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional, Callable
import logging
import functools
import asyncio
from datetime import datetime

from lib.permissions import UserRole, Permission, check_access
from lib.pricing import PlanType, CreditType, QuotaManager, PricingConfig

logger = logging.getLogger(__name__)

class RBACMiddleware:
    """Role-Based Access Control middleware"""
    
    def __init__(self):
        self.security = HTTPBearer(auto_error=False)
    
    async def verify_user_token(self, credentials: HTTPAuthorizationCredentials) -> Dict[str, Any]:
        """Verify JWT token and extract user info"""
        if not credentials:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # This would integrate with your JWT verification
        # For now, return mock user data
        return {
            "user_id": "user_123",
            "org_id": "org_456", 
            "role": UserRole.DEV,
            "plan": PlanType.DEV,
            "email": "developer@example.com"
        }
    
    def require_auth(self) -> Callable:
        """Dependency that requires authentication"""
        async def auth_dependency(request: Request, credentials: HTTPAuthorizationCredentials = Depends(self.security)):
            user_info = await self.verify_user_token(credentials)
            request.state.user = user_info
            return user_info
        return auth_dependency
    
    def require_permission(self, permission: Permission) -> Callable:
        """Dependency that requires specific permission"""
        async def permission_dependency(request: Request, user: Dict[str, Any] = Depends(self.require_auth())):
            user_role = user.get("role", UserRole.DEV)
            
            if not check_access(user_role, permission.value.split("_")[0], permission.value.split("_")[1]):
                logger.warning(f"Permission denied: {user_role} lacks {permission} for {request.url.path}")
                raise HTTPException(
                    status_code=403, 
                    detail={
                        "error": "insufficient_permissions",
                        "message": f"Your {user_role} role does not have {permission} permission",
                        "required_permission": permission.value,
                        "upgrade_url": "/settings/billing"
                    }
                )
            
            return user
        return permission_dependency
    
    def require_role(self, *allowed_roles: UserRole) -> Callable:
        """Dependency that requires specific role(s)"""
        async def role_dependency(request: Request, user: Dict[str, Any] = Depends(self.require_auth())):
            user_role = user.get("role", UserRole.DEV)
            
            if user_role not in allowed_roles:
                logger.warning(f"Role access denied: {user_role} not in {allowed_roles} for {request.url.path}")
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "insufficient_role",
                        "message": f"Access requires one of: {[role.value for role in allowed_roles]}",
                        "current_role": user_role.value,
                        "upgrade_url": "/settings/billing"
                    }
                )
            
            return user
        return role_dependency

class QuotaMiddleware:
    """Usage quota and credits enforcement middleware"""
    
    def __init__(self):
        self.quota_manager = None  # Will be initialized with DB session
    
    async def get_quota_manager(self, request: Request) -> QuotaManager:
        """Get quota manager with DB session"""
        if not hasattr(request.state, "quota_manager"):
            # This would use your actual DB session
            request.state.quota_manager = QuotaManager(None)  # Mock for now
        return request.state.quota_manager
    
    def require_quota(self, feature: str, credits_per_use: int = 1) -> Callable:
        """Dependency that checks and consumes quota/credits"""
        async def quota_dependency(
            request: Request,
            user: Dict[str, Any] = Depends(RBACMiddleware().require_auth()),
            quota_manager: QuotaManager = Depends(self.get_quota_manager)
        ):
            org_id = user.get("org_id")
            user_plan = user.get("plan", PlanType.DEV)
            
            # Check if plan allows this feature
            if not PricingConfig.can_access_feature(user_plan, feature):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "feature_not_available",
                        "message": f"Your {user_plan.value} plan does not include {feature}",
                        "feature": feature,
                        "upgrade_url": "/settings/billing"
                    }
                )
            
            # Check quota/credits
            quota_check = await quota_manager.check_quota(org_id, feature)
            
            if not quota_check["has_quota"]:
                # Check if credits are available
                if quota_check["can_buy_credits"]:
                    raise HTTPException(
                        status_code=402,  # Payment Required
                        detail={
                            "error": "quota_exceeded",
                            "message": f"Monthly {feature} quota exceeded",
                            "remaining": quota_check["remaining"],
                            "limit": quota_check["limit"],
                            "reset_date": quota_check["reset_date"],
                            "credits_available": True,
                            "buy_credits_url": "/settings/credits"
                        }
                    )
                else:
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "error": "quota_exceeded_no_credits",
                            "message": f"Monthly {feature} quota exceeded and credits not available",
                            "upgrade_url": "/settings/billing"
                        }
                    )
            
            # Consume quota
            consumed = await quota_manager.consume_quota(org_id, feature, credits_per_use)
            if not consumed:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to consume quota"
                )
            
            # Add usage info to request state
            request.state.quota_used = {
                "feature": feature,
                "amount": credits_per_use,
                "remaining": quota_check["remaining"] - credits_per_use
            }
            
            return user
        return quota_dependency

class AuditMiddleware:
    """Audit logging for API actions"""
    
    def __init__(self):
        self.audit_log = []
    
    async def log_action(
        self,
        request: Request,
        user_id: str,
        org_id: str,
        action: str,
        resource: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log user action for audit trail"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "org_id": org_id,
            "action": action,
            "resource": resource,
            "success": success,
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "details": details or {}
        }
        
        # In production, this would write to database or log aggregation service
        self.audit_log.append(audit_entry)
        logger.info(f"Audit: {user_id} {action} {resource} - {'success' if success else 'failed'}")
    
    def audit_action(self, action: str, resource: str) -> Callable:
        """Decorator to audit API actions"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract request and user from dependencies
                request = None
                user = None
                
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                if hasattr(request, "state") and hasattr(request.state, "user"):
                    user = request.state.user
                
                user_id = user.get("user_id", "unknown") if user else "unknown"
                org_id = user.get("org_id", "unknown") if user else "unknown"
                
                try:
                    result = await func(*args, **kwargs)
                    await self.log_action(request, user_id, org_id, action, resource, True, {
                        "quota_used": getattr(request.state, "quota_used", None) if request else None
                    })
                    return result
                except Exception as e:
                    await self.log_action(request, user_id, org_id, action, resource, False, {
                        "error": str(e)
                    })
                    raise
            return wrapper
        return decorator

# Global middleware instances
rbac_middleware = RBACMiddleware()
quota_middleware = QuotaMiddleware()
audit_middleware = AuditMiddleware()

# Convenience decorators
require_auth = rbac_middleware.require_auth
require_permission = rbac_middleware.require_permission
require_role = rbac_middleware.require_role
require_quota = quota_middleware.require_quota
audit_action = audit_middleware.audit_action

# Common permission dependencies
require_dev_or_consultant = require_role(UserRole.DEV, UserRole.CON)
require_consultant = require_role(UserRole.CON)
require_landowner = require_role(UserRole.OWN)
require_authority = require_role(UserRole.AUTH)
require_admin = require_role(UserRole.ADM)

# Common feature quota dependencies
require_ai_quota = require_quota("planning_ai", 1)
require_docs_quota = require_quota("auto_docs", 1)
require_bundle_quota = require_quota("submission_bundles", 1)

def enforce_endpoint(
    permission: Permission,
    feature: Optional[str] = None,
    credits_per_use: int = 1,
    audit_action_name: str = None,
    audit_resource: str = None
) -> Callable:
    """
    Comprehensive endpoint enforcement combining RBAC, quota, and audit
    
    Args:
        permission: Required permission
        feature: Feature name for quota checking (optional)
        credits_per_use: Credits consumed per use
        audit_action_name: Action name for audit log
        audit_resource: Resource name for audit log
    """
    def decorator(func: Callable) -> Callable:
        # Apply all middleware in order
        if audit_action_name and audit_resource:
            func = audit_action(audit_action_name, audit_resource)(func)
        
        if feature:
            func = require_quota(feature, credits_per_use)(func)
        
        func = require_permission(permission)(func)
        
        return func
    return decorator

# Export everything
__all__ = [
    "RBACMiddleware",
    "QuotaMiddleware", 
    "AuditMiddleware",
    "rbac_middleware",
    "quota_middleware",
    "audit_middleware",
    "require_auth",
    "require_permission",
    "require_role",
    "require_quota",
    "audit_action",
    "require_dev_or_consultant",
    "require_consultant",
    "require_landowner",
    "require_authority",
    "require_admin",
    "require_ai_quota",
    "require_docs_quota",
    "require_bundle_quota",
    "enforce_endpoint"
]