"""
Credit Enforcement Middleware
Defines exact endpoints that decrement credits with server-side enforcement
"""

from typing import Dict, Set, Optional
from fastapi import Request, HTTPException
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class CreditType(str, Enum):
    """Credit types that can be decremented"""
    AI_ANALYSIS = "AI_ANALYSIS"
    AUTO_DOCS = "AUTO_DOCS"
    SUBMISSION_BUNDLES = "SUBMISSION_BUNDLES"

# Exact endpoints that decrement credits (server-side enforced)
CREDIT_ENFORCEMENT_MAP: Dict[str, Dict[str, int]] = {
    # AI Analysis Credits (1 credit per call)
    "POST /api/planning/analyse": {
        "credit_type": CreditType.AI_ANALYSIS,
        "credit_cost": 1,
        "description": "Planning AI analysis"
    },
    "POST /api/planning/variants": {
        "credit_type": CreditType.AI_ANALYSIS,
        "credit_cost": 1,
        "description": "Scheme variant generation"
    },
    "POST /api/planning/copilot/chat": {
        "credit_type": CreditType.AI_ANALYSIS,
        "credit_cost": 1,
        "description": "Planning Copilot conversation"
    },
    "POST /api/viability/calculate": {
        "credit_type": CreditType.AI_ANALYSIS,
        "credit_cost": 1,
        "description": "Development viability calculation"
    },
    "POST /api/legislation/impact-analysis": {
        "credit_type": CreditType.AI_ANALYSIS,
        "credit_cost": 1,
        "description": "Legislation impact analysis"
    },
    
    # Document Generation Credits (1 credit per document)
    "POST /api/docs/generate": {
        "credit_type": CreditType.AUTO_DOCS,
        "credit_cost": 1,
        "description": "Automated document generation"
    },
    "POST /api/docs/planning-statement": {
        "credit_type": CreditType.AUTO_DOCS,
        "credit_cost": 1,
        "description": "Planning statement generation"
    },
    "POST /api/docs/heritage-statement": {
        "credit_type": CreditType.AUTO_DOCS,
        "credit_cost": 1,
        "description": "Heritage statement generation"
    },
    "POST /api/docs/design-access-statement": {
        "credit_type": CreditType.AUTO_DOCS,
        "credit_cost": 1,
        "description": "Design & Access statement generation"
    },
    
    # Submission Bundle Credits (1 credit per bundle)
    "POST /api/submission-pack/create": {
        "credit_type": CreditType.SUBMISSION_BUNDLES,
        "credit_cost": 1,
        "description": "Submission pack creation"
    },
    "POST /api/submission/council-submit": {
        "credit_type": CreditType.SUBMISSION_BUNDLES,
        "credit_cost": 1,
        "description": "Direct council submission"
    },
    
    # Project Creation (not credits, but quota-limited)
    "POST /api/projects": {
        "quota_type": "projects_total",
        "description": "New project creation"
    }
}

class CreditEnforcementMiddleware:
    """Middleware to enforce credit deductions on specific endpoints"""
    
    def __init__(self):
        self.enforcement_rules = CREDIT_ENFORCEMENT_MAP
    
    async def check_and_deduct_credits(self, 
                                     request: Request, 
                                     user_id: str, 
                                     org_id: str) -> bool:
        """
        Check if user has sufficient credits and deduct if endpoint requires it
        
        Returns:
            bool: True if allowed to proceed, False if insufficient credits
        """
        route_key = f"{request.method} {request.url.path}"
        
        # Check if this endpoint requires credit deduction
        if route_key not in self.enforcement_rules:
            return True  # No credits required for this endpoint
        
        rule = self.enforcement_rules[route_key]
        
        # If it's quota-limited (not credit-based)
        if "quota_type" in rule:
            return await self._check_quota_limit(user_id, org_id, rule["quota_type"])
        
        # If it's credit-based
        credit_type = rule["credit_type"]
        credit_cost = rule["credit_cost"]
        
        # Check current credit balance
        current_credits = await self._get_user_credits(org_id, credit_type)
        
        if current_credits < credit_cost:
            logger.warning(f"Insufficient credits for {route_key}: need {credit_cost}, have {current_credits}")
            raise HTTPException(
                status_code=402,  # Payment Required
                detail={
                    "error": "insufficient_credits",
                    "credit_type": credit_type,
                    "required": credit_cost,
                    "available": current_credits,
                    "description": rule["description"]
                }
            )
        
        # Deduct credits
        await self._deduct_credits(org_id, credit_type, credit_cost)
        
        # Log the transaction
        await self._log_credit_usage(user_id, org_id, route_key, credit_type, credit_cost)
        
        return True
    
    async def _get_user_credits(self, org_id: str, credit_type: CreditType) -> int:
        """Get current credit balance for organization"""
        from lib.quota import QuotaManager
        
        quota_manager = QuotaManager()
        return await quota_manager.get_credit_balance(org_id, credit_type)
    
    async def _deduct_credits(self, org_id: str, credit_type: CreditType, amount: int):
        """Deduct credits from organization balance"""
        from lib.quota import QuotaManager
        
        quota_manager = QuotaManager()
        await quota_manager.deduct_credits(org_id, credit_type, amount)
    
    async def _check_quota_limit(self, user_id: str, org_id: str, quota_type: str) -> bool:
        """Check if user is within quota limits"""
        from lib.quota import QuotaManager
        
        quota_manager = QuotaManager()
        return await quota_manager.check_quota_limit(org_id, quota_type)
    
    async def _log_credit_usage(self, 
                               user_id: str, 
                               org_id: str, 
                               endpoint: str,
                               credit_type: CreditType, 
                               amount: int):
        """Log credit usage for audit trail"""
        from lib.audit import AuditLogger
        
        audit_logger = AuditLogger()
        await audit_logger.log_credit_usage(
            user_id=user_id,
            org_id=org_id,
            endpoint=endpoint,
            credit_type=credit_type,
            amount=amount
        )

# Decorator for easy endpoint protection
def requires_credits(credit_type: CreditType, cost: int = 1):
    """Decorator to mark endpoints that require credit deduction"""
    def decorator(func):
        func._requires_credits = True
        func._credit_type = credit_type
        func._credit_cost = cost
        return func
    return decorator

# Export enforcement rules for documentation
def get_credit_enforcement_rules() -> Dict[str, Dict]:
    """Get all credit enforcement rules for documentation"""
    return CREDIT_ENFORCEMENT_MAP.copy()

def get_endpoints_by_credit_type(credit_type: CreditType) -> Set[str]:
    """Get all endpoints that use a specific credit type"""
    return {
        endpoint for endpoint, rule in CREDIT_ENFORCEMENT_MAP.items()
        if rule.get("credit_type") == credit_type
    }