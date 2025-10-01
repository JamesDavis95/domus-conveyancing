"""
Backend Authentication Configuration
Defines user roles, plan types, and quota limits for the platform
"""

from enum import Enum
from typing import Dict, Any

class UserRole(Enum):
    DEVELOPER = "developer"
    CONSULTANT = "consultant" 
    LANDOWNER = "landowner"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    SUPER_ADMIN = "super_admin"

class PlanType(Enum):
    CORE = "core"           # £29/month - Basic planning tools
    PROFESSIONAL = "professional"  # £99/month - Full planning suite
    ENTERPRISE = "enterprise"      # £299/month - Unlimited + priority support

# Quota limits by plan type
PLAN_LIMITS = {
    PlanType.CORE: {
        "site_analyses": 10,        # 10 AI site analyses per month
        "documents": 5,             # 5 auto-generated documents per month
        "api_calls": 1000,          # 1,000 property API calls per month
        "bng_listings": 2,          # 2 BNG marketplace listings
        "support_tickets": 3,       # 3 support tickets per month
        "users": 2                  # 2 users per organization
    },
    PlanType.PROFESSIONAL: {
        "site_analyses": 50,        # 50 AI site analyses per month
        "documents": 25,            # 25 auto-generated documents per month
        "api_calls": 10000,         # 10,000 property API calls per month
        "bng_listings": 10,         # 10 BNG marketplace listings
        "support_tickets": 10,      # 10 support tickets per month
        "users": 10                 # 10 users per organization
    },
    PlanType.ENTERPRISE: {
        "site_analyses": -1,        # Unlimited AI site analyses
        "documents": -1,            # Unlimited auto-generated documents
        "api_calls": -1,            # Unlimited property API calls
        "bng_listings": -1,         # Unlimited BNG marketplace listings
        "support_tickets": -1,      # Unlimited support tickets
        "users": -1                 # Unlimited users per organization
    }
}

# Plan pricing (in pence for Stripe)
PLAN_PRICING = {
    PlanType.CORE: {
        "amount": 2900,  # £29.00
        "currency": "gbp",
        "interval": "month",
        "name": "Core Plan",
        "description": "Essential planning tools for small projects"
    },
    PlanType.PROFESSIONAL: {
        "amount": 9900,  # £99.00
        "currency": "gbp", 
        "interval": "month",
        "name": "Professional Plan",
        "description": "Complete planning intelligence suite"
    },
    PlanType.ENTERPRISE: {
        "amount": 29900,  # £299.00
        "currency": "gbp",
        "interval": "month", 
        "name": "Enterprise Plan",
        "description": "Unlimited access with priority support"
    }
}

# Feature permissions by role
ROLE_PERMISSIONS = {
    UserRole.DEVELOPER: {
        "planning_ai": True,
        "auto_docs": True,
        "property_api": True,
        "bng_marketplace_buy": True,
        "bng_marketplace_sell": False,
        "admin_panel": False,
        "organization_management": False
    },
    UserRole.CONSULTANT: {
        "planning_ai": True,
        "auto_docs": True,
        "property_api": True,
        "bng_marketplace_buy": True,
        "bng_marketplace_sell": True,
        "admin_panel": False,
        "organization_management": True
    },
    UserRole.LANDOWNER: {
        "planning_ai": False,
        "auto_docs": False,
        "property_api": False,
        "bng_marketplace_buy": False,
        "bng_marketplace_sell": True,
        "admin_panel": False,
        "organization_management": False
    },
    UserRole.ADMIN: {
        "planning_ai": True,
        "auto_docs": True,
        "property_api": True,
        "bng_marketplace_buy": True,
        "bng_marketplace_sell": True,
        "admin_panel": True,
        "organization_management": True
    },
    UserRole.SUPER_ADMIN: {
        "planning_ai": True,
        "auto_docs": True,
        "property_api": True,
        "bng_marketplace_buy": True,
        "bng_marketplace_sell": True,
        "admin_panel": True,
        "organization_management": True,
        "platform_administration": True,
        "billing_management": True,
        "user_impersonation": True
    }
}

def has_permission(user_role: UserRole, permission: str) -> bool:
    """Check if user role has specific permission"""
    permissions = ROLE_PERMISSIONS.get(user_role, {})
    return permissions.get(permission, False)

def get_plan_features(plan_type: PlanType) -> Dict[str, Any]:
    """Get features and limits for a plan type"""
    limits = PLAN_LIMITS.get(plan_type, {})
    pricing = PLAN_PRICING.get(plan_type, {})
    
    return {
        "limits": limits,
        "pricing": pricing,
        "features": {
            "ai_planning_analysis": True,
            "document_generation": True,
            "property_data_api": True,
            "bng_marketplace": True,
            "priority_support": plan_type == PlanType.ENTERPRISE,
            "white_label": plan_type == PlanType.ENTERPRISE,
            "api_access": plan_type in [PlanType.PROFESSIONAL, PlanType.ENTERPRISE],
            "bulk_operations": plan_type == PlanType.ENTERPRISE
        }
    }