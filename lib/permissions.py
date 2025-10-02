"""
RBAC Permission System - Core of Domus Platform Security
Defines roles, features, and permission mappings per blueprint specification
"""
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass

class Role(Enum):
    """User roles as defined in master blueprint"""
    DEV = "developer"           # Developer / Promoter
    CON = "consultant"          # Consultant / Planner
    OWN = "landowner"          # Landowner
    AUTH = "authority"         # Authority / Council (token review, read-only)
    ADM = "admin"              # Admin

class Feature(Enum):
    """Features that can be accessed based on role permissions"""
    # Core Planning Services
    PROJECTS = "projects"
    PLANNING_AI = "planning_ai"
    AUTODOCS = "autodocs"
    DOCUMENTS = "documents"
    
    # Marketplace
    MKT_SUPPLY = "marketplace_supply"
    MKT_DEMAND = "marketplace_demand"
    CONTRACTS = "contracts"
    
    # Analytics & Management
    ANALYTICS = "analytics"
    SETTINGS = "settings"
    BILLING = "billing"
    API_KEYS = "api_keys"
    
    # Admin & Authority
    ADMIN = "admin"
    AUTH_PORTAL = "authority_portal"

class PlanType(Enum):
    """Subscription plan types with different quotas"""
    DEMO = "demo"
    PRO = "pro"
    ENTERPRISE = "enterprise"

# Role → Features mapping (exactly as specified in blueprint)
ROLE_FEATURES: Dict[Role, List[Feature]] = {
    Role.DEV: [
        Feature.PROJECTS, Feature.PLANNING_AI, Feature.AUTODOCS, Feature.DOCUMENTS,
        Feature.MKT_DEMAND, Feature.CONTRACTS, Feature.ANALYTICS, 
        Feature.SETTINGS, Feature.BILLING
    ],
    Role.CON: [
        Feature.PROJECTS, Feature.PLANNING_AI, Feature.AUTODOCS, Feature.DOCUMENTS,
        Feature.MKT_DEMAND, Feature.CONTRACTS, Feature.ANALYTICS,
        Feature.SETTINGS, Feature.BILLING
    ],
    Role.OWN: [
        Feature.MKT_SUPPLY, Feature.CONTRACTS, Feature.ANALYTICS,
        Feature.SETTINGS, Feature.BILLING
    ],
    Role.AUTH: [
        Feature.AUTH_PORTAL
    ],
    Role.ADM: [
        Feature.PROJECTS, Feature.PLANNING_AI, Feature.AUTODOCS, Feature.DOCUMENTS,
        Feature.MKT_SUPPLY, Feature.MKT_DEMAND, Feature.CONTRACTS, Feature.ANALYTICS,
        Feature.SETTINGS, Feature.BILLING, Feature.API_KEYS, Feature.ADMIN
    ]
}

# Plan quotas (exactly as specified in blueprint)
PLAN_QUOTAS = {
    PlanType.DEMO: {
        "projects": 1,
        "docs": 1,
        "marketplace_posts": 0,
        "contracts": 0
    },
    PlanType.PRO: {
        "projects": 10,
        "docs": 50,
        "marketplace_posts": 5,
        "contracts": 10
    },
    PlanType.ENTERPRISE: {
        "projects": -1,  # unlimited
        "docs": -1,      # unlimited
        "marketplace_posts": -1,
        "contracts": -1
    }
}

@dataclass
class UserContext:
    """User context for permission checks"""
    user_id: int
    org_id: int
    role: Role
    plan: PlanType
    is_active: bool = True

def has_feature_access(user_role: Role, feature: Feature) -> bool:
    """Check if a role has access to a specific feature"""
    return feature in ROLE_FEATURES.get(user_role, [])

def get_accessible_features(user_role: Role) -> List[Feature]:
    """Get all features accessible to a role"""
    return ROLE_FEATURES.get(user_role, [])

def check_quota_limit(plan: PlanType, quota_type: str, current_usage: int) -> bool:
    """Check if plan quota allows more usage"""
    quota_limits = PLAN_QUOTAS.get(plan, {})
    limit = quota_limits.get(quota_type, 0)
    
    # Unlimited quota (-1)
    if limit == -1:
        return True
    
    # Check if under limit
    return current_usage < limit

def get_quota_info(plan: PlanType, quota_type: str, current_usage: int) -> Dict:
    """Get quota information for display"""
    quota_limits = PLAN_QUOTAS.get(plan, {})
    limit = quota_limits.get(quota_type, 0)
    
    return {
        "current": current_usage,
        "limit": limit,
        "unlimited": limit == -1,
        "percentage": 0 if limit == -1 else (current_usage / limit * 100) if limit > 0 else 100,
        "available": limit - current_usage if limit != -1 else -1
    }

# Feature → Route mapping for UI navigation
FEATURE_ROUTES = {
    Feature.PROJECTS: "/projects",
    Feature.PLANNING_AI: "/planning-ai", 
    Feature.AUTODOCS: "/auto-docs",
    Feature.DOCUMENTS: "/documents",
    Feature.MKT_SUPPLY: "/marketplace/supply",
    Feature.MKT_DEMAND: "/marketplace/demand", 
    Feature.CONTRACTS: "/contracts",
    Feature.ANALYTICS: "/analytics",
    Feature.SETTINGS: "/settings",
    Feature.BILLING: "/settings/billing",
    Feature.API_KEYS: "/settings/api-keys",
    Feature.ADMIN: "/admin",
    Feature.AUTH_PORTAL: "/authority"
}

# Sidebar menu structure (role-filtered)
SIDEBAR_SECTIONS = [
    {
        "title": "Dashboard",
        "icon": "dashboard",
        "route": "/dashboard",
        "features": []  # Available to all authenticated users
    },
    {
        "title": "Projects",
        "icon": "folder",
        "route": "/projects",
        "features": [Feature.PROJECTS]
    },
    {
        "title": "Planning Services",
        "icon": "lightbulb",
        "submenu": [
            {"title": "Planning AI", "route": "/planning-ai", "features": [Feature.PLANNING_AI]},
            {"title": "Auto-Docs", "route": "/auto-docs", "features": [Feature.AUTODOCS]},
            {"title": "Documents Hub", "route": "/documents", "features": [Feature.DOCUMENTS]}
        ]
    },
    {
        "title": "Marketplace",
        "icon": "store",
        "submenu": [
            {"title": "Supply Listings", "route": "/marketplace/supply", "features": [Feature.MKT_SUPPLY]},
            {"title": "Demand Posts", "route": "/marketplace/demand", "features": [Feature.MKT_DEMAND]},
            {"title": "Contracts", "route": "/contracts", "features": [Feature.CONTRACTS]}
        ]
    },
    {
        "title": "Analytics",
        "icon": "chart",
        "route": "/analytics", 
        "features": [Feature.ANALYTICS]
    },
    {
        "title": "Settings",
        "icon": "settings",
        "submenu": [
            {"title": "Profile", "route": "/settings", "features": [Feature.SETTINGS]},
            {"title": "Billing", "route": "/settings/billing", "features": [Feature.BILLING]},
            {"title": "API Keys", "route": "/settings/api-keys", "features": [Feature.API_KEYS]}
        ]
    },
    {
        "title": "Admin", 
        "icon": "shield",
        "route": "/admin",
        "features": [Feature.ADMIN]
    }
]

def filter_sidebar_for_role(user_role: Role) -> List[Dict]:
    """Filter sidebar sections based on user role permissions"""
    accessible_features = get_accessible_features(user_role)
    filtered_sections = []
    
    for section in SIDEBAR_SECTIONS:
        # Check if section has feature requirements
        section_features = section.get("features", [])
        
        # If no features required (like Dashboard), include it
        if not section_features:
            filtered_sections.append(section)
            continue
            
        # Check if user has access to section features
        if any(feature in accessible_features for feature in section_features):
            # For sections with submenus, filter submenu items
            if "submenu" in section:
                filtered_submenu = []
                for item in section["submenu"]:
                    item_features = item.get("features", [])
                    if any(feature in accessible_features for feature in item_features):
                        filtered_submenu.append(item)
                
                if filtered_submenu:
                    section_copy = section.copy()
                    section_copy["submenu"] = filtered_submenu
                    filtered_sections.append(section_copy)
            else:
                filtered_sections.append(section)
    
    return filtered_sections