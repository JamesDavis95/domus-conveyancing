"""
Role-Based Access Control (RBAC) System
Single source of truth for all permissions and access control
"""

from enum import Enum
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

class UserRole(str, Enum):
    """User roles in the system"""
    DEV = "DEV"           # Developer
    CON = "CON"           # Consultant  
    OWN = "OWN"           # Landowner
    AUTH = "AUTH"         # Authority
    ADM = "ADM"           # Admin

class Permission(str, Enum):
    """Granular permissions"""
    # Project management
    VIEW_PROJECTS = "view_projects"
    CREATE_PROJECTS = "create_projects"
    EDIT_PROJECTS = "edit_projects"
    DELETE_PROJECTS = "delete_projects"
    
    # Planning AI
    USE_PLANNING_AI = "use_planning_ai"
    VIEW_AI_ANALYSIS = "view_ai_analysis"
    EXPORT_AI_ANALYSIS = "export_ai_analysis"
    
    # Documents
    GENERATE_DOCS = "generate_docs"
    VIEW_DOCS = "view_docs"
    EDIT_DOCS = "edit_docs"
    DELETE_DOCS = "delete_docs"
    GENERATE_ADVANCED_DOCS = "generate_advanced_docs"
    
    # Submission packs
    CREATE_SUBMISSION_PACK = "create_submission_pack"
    VIEW_SUBMISSION_PACK = "view_submission_pack"
    EDIT_SUBMISSION_PACK = "edit_submission_pack"
    SUBMIT_TO_COUNCIL = "submit_to_council"
    
    # Marketplace
    VIEW_MARKETPLACE_DEMAND = "view_marketplace_demand"
    CREATE_MARKETPLACE_DEMAND = "create_marketplace_demand"
    VIEW_MARKETPLACE_SUPPLY = "view_marketplace_supply"
    CREATE_MARKETPLACE_SUPPLY = "create_marketplace_supply"
    MANAGE_MARKETPLACE_LISTINGS = "manage_marketplace_listings"
    
    # Contracts
    VIEW_CONTRACTS = "view_contracts"
    CREATE_CONTRACTS = "create_contracts"
    EDIT_CONTRACTS = "edit_contracts"
    SIGN_CONTRACTS = "sign_contracts"
    
    # Analytics
    VIEW_BASIC_ANALYTICS = "view_basic_analytics"
    VIEW_FULL_ANALYTICS = "view_full_analytics"
    VIEW_LPA_ANALYTICS = "view_lpa_analytics"
    VIEW_ORG_INSIGHTS = "view_org_insights"
    
    # Appeals & Objections
    VIEW_APPEALS = "view_appeals"
    CREATE_APPEALS = "create_appeals"
    VIEW_OBJECTIONS = "view_objections"
    ANALYZE_OBJECTIONS = "analyze_objections"
    
    # New Premium Modules
    USE_VIABILITY_CALC = "use_viability_calc"
    USE_SCHEME_OPTIMISER = "use_scheme_optimiser"
    USE_LEGISLATION_TRACKER = "use_legislation_tracker"
    USE_PLANNING_COPILOT = "use_planning_copilot"
    ACCESS_PREMIUM_MODULES = "access_premium_modules"
    ACCESS_APP_FEATURES = "access_app_features"
    
    # General access permissions
    VIEW_PROFILE = "view_profile"
    VIEW_BILLING = "view_billing"
    VIEW_PROPERTY_DATA = "view_property_data"
    ACCESS_AUTHORITY_PORTAL = "access_authority_portal"
    ADMIN_ACCESS = "admin_access"
    
    # Settings & Admin
    VIEW_SETTINGS = "view_settings"
    EDIT_SETTINGS = "edit_settings"
    MANAGE_BILLING = "manage_billing"
    MANAGE_CREDITS = "manage_credits"
    MANAGE_SECURITY = "manage_security"
    
    # Authority access
    VIEW_AUTHORITY_PORTAL = "view_authority_portal"
    COMMENT_ON_SUBMISSIONS = "comment_on_submissions"
    
    # Admin functions
    MANAGE_USERS = "manage_users"
    MANAGE_ORGANIZATIONS = "manage_organizations"
    VIEW_SYSTEM_LOGS = "view_system_logs"
    MANAGE_SYSTEM_CONFIG = "manage_system_config"

@dataclass
class RolePermissions:
    """Permissions assigned to a role"""
    role: UserRole
    permissions: Set[Permission]
    description: str

class PermissionsMatrix:
    """Central permissions matrix - single source of truth"""
    
    ROLE_PERMISSIONS = {
        UserRole.DEV: RolePermissions(
            role=UserRole.DEV,
            permissions={
                # Projects
                Permission.VIEW_PROJECTS,
                Permission.CREATE_PROJECTS,
                Permission.EDIT_PROJECTS,
                Permission.DELETE_PROJECTS,
                
                # Planning AI
                Permission.USE_PLANNING_AI,
                Permission.VIEW_AI_ANALYSIS,
                Permission.EXPORT_AI_ANALYSIS,
                
                # Documents (basic)
                Permission.GENERATE_DOCS,
                Permission.VIEW_DOCS,
                Permission.EDIT_DOCS,
                Permission.DELETE_DOCS,
                
                # Submission packs
                Permission.CREATE_SUBMISSION_PACK,
                Permission.VIEW_SUBMISSION_PACK,
                Permission.EDIT_SUBMISSION_PACK,
                Permission.SUBMIT_TO_COUNCIL,
                
                # Marketplace (demand side)
                Permission.VIEW_MARKETPLACE_DEMAND,
                Permission.CREATE_MARKETPLACE_DEMAND,
                
                # Contracts
                Permission.VIEW_CONTRACTS,
                Permission.CREATE_CONTRACTS,
                Permission.EDIT_CONTRACTS,
                Permission.SIGN_CONTRACTS,
                
                # Analytics (basic)
                Permission.VIEW_BASIC_ANALYTICS,
                
                # New Premium Modules
                Permission.USE_VIABILITY_CALC,
                Permission.USE_SCHEME_OPTIMISER,
                Permission.USE_PLANNING_COPILOT,
                
                # General access
                Permission.VIEW_PROFILE,
                Permission.VIEW_BILLING,
                Permission.VIEW_PROPERTY_DATA,
                
                # Settings
                Permission.VIEW_SETTINGS,
                Permission.EDIT_SETTINGS,
                Permission.MANAGE_BILLING,
                Permission.MANAGE_CREDITS,
                Permission.MANAGE_SECURITY
            },
            description="Developer with project management and planning tools"
        ),
        
        UserRole.CON: RolePermissions(
            role=UserRole.CON,
            permissions={
                # All DEV permissions plus...
                Permission.VIEW_PROJECTS,
                Permission.CREATE_PROJECTS,
                Permission.EDIT_PROJECTS,
                Permission.DELETE_PROJECTS,
                Permission.USE_PLANNING_AI,
                Permission.VIEW_AI_ANALYSIS,
                Permission.EXPORT_AI_ANALYSIS,
                Permission.GENERATE_DOCS,
                Permission.VIEW_DOCS,
                Permission.EDIT_DOCS,
                Permission.DELETE_DOCS,
                Permission.CREATE_SUBMISSION_PACK,
                Permission.VIEW_SUBMISSION_PACK,
                Permission.EDIT_SUBMISSION_PACK,
                Permission.SUBMIT_TO_COUNCIL,
                Permission.VIEW_MARKETPLACE_DEMAND,
                Permission.CREATE_MARKETPLACE_DEMAND,
                Permission.VIEW_CONTRACTS,
                Permission.CREATE_CONTRACTS,
                Permission.EDIT_CONTRACTS,
                Permission.SIGN_CONTRACTS,
                Permission.VIEW_SETTINGS,
                Permission.EDIT_SETTINGS,
                Permission.MANAGE_BILLING,
                Permission.MANAGE_CREDITS,
                Permission.MANAGE_SECURITY,
                
                # Advanced consultant features
                Permission.GENERATE_ADVANCED_DOCS,
                Permission.VIEW_APPEALS,
                Permission.CREATE_APPEALS,
                Permission.VIEW_OBJECTIONS,
                Permission.ANALYZE_OBJECTIONS,
                Permission.VIEW_FULL_ANALYTICS,
                Permission.VIEW_LPA_ANALYTICS,
                Permission.VIEW_ORG_INSIGHTS,
                
                # Premium modules (consultant tier)
                Permission.USE_VIABILITY_CALC,
                Permission.USE_SCHEME_OPTIMISER,
                Permission.USE_LEGISLATION_TRACKER,
                Permission.USE_PLANNING_COPILOT,
                Permission.SUBMIT_TO_COUNCIL,
                Permission.ACCESS_PREMIUM_MODULES,
                Permission.VIEW_PROFILE,
                Permission.VIEW_BILLING,
                Permission.VIEW_PROPERTY_DATA,
                Permission.ACCESS_APP_FEATURES
            },
            description="Full-featured consultant with advanced tools"
        ),
        
        UserRole.OWN: RolePermissions(
            role=UserRole.OWN,
            permissions={
                # Marketplace (supply side only)
                Permission.VIEW_MARKETPLACE_SUPPLY,
                Permission.CREATE_MARKETPLACE_SUPPLY,
                Permission.MANAGE_MARKETPLACE_LISTINGS,
                
                # Contracts (own only)
                Permission.VIEW_CONTRACTS,
                Permission.SIGN_CONTRACTS,
                
                # Basic analytics (supply focused)
                Permission.VIEW_BASIC_ANALYTICS,
                
                # Settings
                Permission.VIEW_SETTINGS,
                Permission.EDIT_SETTINGS,
                Permission.MANAGE_BILLING,
                
                # Basic access
                Permission.VIEW_PROFILE,
                Permission.ACCESS_APP_FEATURES
            },
            description="Landowner with marketplace and contract access"
        ),
        
        UserRole.AUTH: RolePermissions(
            role=UserRole.AUTH,
            permissions={
                # Authority portal access
                Permission.VIEW_AUTHORITY_PORTAL,
                Permission.VIEW_SUBMISSION_PACK,
                Permission.COMMENT_ON_SUBMISSIONS,
                
                # Basic access
                Permission.VIEW_PROFILE,
                Permission.ACCESS_APP_FEATURES
            },
            description="Planning authority with submission review access"
        ),
        
        UserRole.ADM: RolePermissions(
            role=UserRole.ADM,
            permissions=set(Permission),  # All permissions
            description="System administrator with full access"
        )
    }
    
    @classmethod
    def get_role_permissions(cls, role: UserRole) -> Set[Permission]:
        """Get all permissions for a role"""
        role_perms = cls.ROLE_PERMISSIONS.get(role)
        return role_perms.permissions if role_perms else set()
    
    @classmethod
    def has_permission(cls, role: UserRole, permission: Permission) -> bool:
        """Check if role has specific permission"""
        return permission in cls.get_role_permissions(role)
    
    @classmethod
    def can_access_route(cls, role: UserRole, route: str) -> bool:
        """Check if role can access specific route"""
        route_permissions = cls._get_route_permissions()
        required_permission = route_permissions.get(route)
        
        if not required_permission:
            return True  # No specific permission required
        
        return cls.has_permission(role, required_permission)
    
    @classmethod
    def _get_route_permissions(cls) -> Dict[str, Permission]:
        """Map routes to required permissions"""
        return {
            # Dashboard
            "/dashboard": Permission.VIEW_PROJECTS,  # Basic access check
            
            # Projects
            "/projects": Permission.VIEW_PROJECTS,
            "/projects/new": Permission.CREATE_PROJECTS,
            "/projects/[id]": Permission.VIEW_PROJECTS,
            "/projects/[id]/edit": Permission.EDIT_PROJECTS,
            "/projects/[id]/viability": Permission.VIEW_PROJECTS,
            "/projects/[id]/bng": Permission.VIEW_PROJECTS,
            "/projects/[id]/transport": Permission.VIEW_PROJECTS,
            "/projects/[id]/environment": Permission.VIEW_PROJECTS,
            "/projects/[id]/appeals": Permission.VIEW_APPEALS,
            "/projects/[id]/collaboration": Permission.VIEW_PROJECTS,
            
            # Planning services
            "/planning-ai": Permission.USE_PLANNING_AI,
            "/auto-docs": Permission.GENERATE_DOCS,
            "/documents": Permission.VIEW_DOCS,
            "/submission-pack": Permission.VIEW_SUBMISSION_PACK,
            
            # Marketplace
            "/marketplace/demand": Permission.VIEW_MARKETPLACE_DEMAND,
            "/marketplace/supply": Permission.VIEW_MARKETPLACE_SUPPLY,
            "/contracts": Permission.VIEW_CONTRACTS,
            
            # Analytics
            "/analytics": Permission.VIEW_BASIC_ANALYTICS,
            "/analytics/lpa": Permission.VIEW_LPA_ANALYTICS,
            "/analytics/org-insights": Permission.VIEW_ORG_INSIGHTS,
            
            # Settings
            "/settings": Permission.VIEW_SETTINGS,
            "/settings/billing": Permission.MANAGE_BILLING,
            "/settings/credits": Permission.MANAGE_CREDITS,
            "/settings/security": Permission.MANAGE_SECURITY,
            
            # Authority
            "/authority/[token]": Permission.VIEW_AUTHORITY_PORTAL
        }

class AccessControl:
    """Runtime access control implementation"""
    
    def __init__(self):
        self.permissions_matrix = PermissionsMatrix()
    
    def check_access(self, user_role: UserRole, resource: str, action: str = "view") -> bool:
        """
        Check if user has access to resource/action
        
        Args:
            user_role: User's role
            resource: Resource being accessed (e.g., "projects", "planning-ai")
            action: Action being performed (e.g., "view", "create", "edit")
        
        Returns:
            bool: True if access allowed
        """
        permission_map = {
            ("projects", "view"): Permission.VIEW_PROJECTS,
            ("projects", "create"): Permission.CREATE_PROJECTS,
            ("projects", "edit"): Permission.EDIT_PROJECTS,
            ("projects", "delete"): Permission.DELETE_PROJECTS,
            
            ("planning-ai", "use"): Permission.USE_PLANNING_AI,
            ("planning-ai", "view"): Permission.VIEW_AI_ANALYSIS,
            ("planning-ai", "export"): Permission.EXPORT_AI_ANALYSIS,
            
            ("documents", "view"): Permission.VIEW_DOCS,
            ("documents", "create"): Permission.GENERATE_DOCS,
            ("documents", "edit"): Permission.EDIT_DOCS,
            ("documents", "create_advanced"): Permission.GENERATE_ADVANCED_DOCS,
            
            ("submission-pack", "view"): Permission.VIEW_SUBMISSION_PACK,
            ("submission-pack", "create"): Permission.CREATE_SUBMISSION_PACK,
            ("submission-pack", "submit"): Permission.SUBMIT_TO_COUNCIL,
            
            ("marketplace-demand", "view"): Permission.VIEW_MARKETPLACE_DEMAND,
            ("marketplace-demand", "create"): Permission.CREATE_MARKETPLACE_DEMAND,
            ("marketplace-supply", "view"): Permission.VIEW_MARKETPLACE_SUPPLY,
            ("marketplace-supply", "create"): Permission.CREATE_MARKETPLACE_SUPPLY,
            
            ("contracts", "view"): Permission.VIEW_CONTRACTS,
            ("contracts", "create"): Permission.CREATE_CONTRACTS,
            ("contracts", "edit"): Permission.EDIT_CONTRACTS,
            ("contracts", "sign"): Permission.SIGN_CONTRACTS,
            
            ("analytics", "view_basic"): Permission.VIEW_BASIC_ANALYTICS,
            ("analytics", "view_full"): Permission.VIEW_FULL_ANALYTICS,
            ("analytics", "view_lpa"): Permission.VIEW_LPA_ANALYTICS,
            ("analytics", "view_insights"): Permission.VIEW_ORG_INSIGHTS,
            
            ("appeals", "view"): Permission.VIEW_APPEALS,
            ("appeals", "create"): Permission.CREATE_APPEALS,
            ("objections", "view"): Permission.VIEW_OBJECTIONS,
            ("objections", "analyze"): Permission.ANALYZE_OBJECTIONS,
            
            ("settings", "view"): Permission.VIEW_SETTINGS,
            ("settings", "edit"): Permission.EDIT_SETTINGS,
            ("billing", "manage"): Permission.MANAGE_BILLING,
            ("credits", "manage"): Permission.MANAGE_CREDITS,
            ("security", "manage"): Permission.MANAGE_SECURITY,
            
            ("authority", "view"): Permission.VIEW_AUTHORITY_PORTAL,
            ("authority", "comment"): Permission.COMMENT_ON_SUBMISSIONS
        }
        
        required_permission = permission_map.get((resource, action))
        if not required_permission:
            logger.warning(f"No permission mapping for {resource}:{action}")
            return False
        
        has_access = self.permissions_matrix.has_permission(user_role, required_permission)
        
        if not has_access:
            logger.warning(f"Access denied: {user_role} lacks {required_permission} for {resource}:{action}")
        
        return has_access
    
    def get_accessible_routes(self, user_role: UserRole) -> List[str]:
        """Get list of routes user can access"""
        accessible_routes = []
        route_permissions = self.permissions_matrix._get_route_permissions()
        user_permissions = self.permissions_matrix.get_role_permissions(user_role)
        
        for route, required_permission in route_permissions.items():
            if required_permission in user_permissions:
                accessible_routes.append(route)
        
        return accessible_routes
    
    def generate_sidebar_menu(self, user_role: UserRole) -> List[Dict[str, Any]]:
        """Generate sidebar menu based on user role"""
        all_menu_items = [
            {
                "title": "Dashboard",
                "href": "/dashboard",
                "icon": "dashboard",
                "permission": Permission.VIEW_PROJECTS
            },
            {
                "title": "Projects",
                "href": "/projects", 
                "icon": "folder",
                "permission": Permission.VIEW_PROJECTS,
                "submenu": [
                    {"title": "All Projects", "href": "/projects"},
                    {"title": "New Project", "href": "/projects/new", "permission": Permission.CREATE_PROJECTS}
                ]
            },
            {
                "title": "Planning Services",
                "icon": "cpu",
                "submenu": [
                    {"title": "Planning AI", "href": "/planning-ai", "permission": Permission.USE_PLANNING_AI},
                    {"title": "Auto-Docs", "href": "/auto-docs", "permission": Permission.GENERATE_DOCS},
                    {"title": "Documents", "href": "/documents", "permission": Permission.VIEW_DOCS},
                    {"title": "Submission Pack", "href": "/submission-pack", "permission": Permission.VIEW_SUBMISSION_PACK}
                ]
            },
            {
                "title": "Marketplace",
                "icon": "store",
                "submenu": [
                    {"title": "Find Land", "href": "/marketplace/demand", "permission": Permission.VIEW_MARKETPLACE_DEMAND},
                    {"title": "List Land", "href": "/marketplace/supply", "permission": Permission.VIEW_MARKETPLACE_SUPPLY},
                    {"title": "Contracts", "href": "/contracts", "permission": Permission.VIEW_CONTRACTS}
                ]
            },
            {
                "title": "Analytics", 
                "icon": "chart",
                "permission": Permission.VIEW_BASIC_ANALYTICS,
                "submenu": [
                    {"title": "Overview", "href": "/analytics", "permission": Permission.VIEW_BASIC_ANALYTICS},
                    {"title": "LPA Insights", "href": "/analytics/lpa", "permission": Permission.VIEW_LPA_ANALYTICS},
                    {"title": "Org Insights", "href": "/analytics/org-insights", "permission": Permission.VIEW_ORG_INSIGHTS}
                ]
            },
            {
                "title": "Settings",
                "href": "/settings",
                "icon": "settings", 
                "permission": Permission.VIEW_SETTINGS,
                "submenu": [
                    {"title": "General", "href": "/settings"},
                    {"title": "Billing", "href": "/settings/billing", "permission": Permission.MANAGE_BILLING},
                    {"title": "Credits", "href": "/settings/credits", "permission": Permission.MANAGE_CREDITS},
                    {"title": "Security", "href": "/settings/security", "permission": Permission.MANAGE_SECURITY}
                ]
            }
        ]
        
        user_permissions = self.permissions_matrix.get_role_permissions(user_role)
        
        def filter_menu_item(item):
            # Check if user has permission for main item
            if "permission" in item and item["permission"] not in user_permissions:
                return None
            
            # Filter submenu items
            if "submenu" in item:
                filtered_submenu = []
                for submenu_item in item["submenu"]:
                    if "permission" not in submenu_item or submenu_item["permission"] in user_permissions:
                        filtered_submenu.append(submenu_item)
                
                if filtered_submenu:
                    item["submenu"] = filtered_submenu
                else:
                    return None  # No accessible submenu items
            
            return item
        
        return [item for item in [filter_menu_item(item) for item in all_menu_items] if item is not None]

# Global access control instance
access_control = AccessControl()

# Helper functions for easy use
def check_access(user_role: UserRole, resource: str, action: str = "view") -> bool:
    """Quick access check"""
    return access_control.check_access(user_role, resource, action)

def has_permission(user_role: UserRole, permission: Permission) -> bool:
    """Quick permission check"""
    return PermissionsMatrix.has_permission(user_role, permission)

def generate_user_menu(user_role: UserRole) -> List[Dict[str, Any]]:
    """Generate menu for user"""
    return access_control.generate_sidebar_menu(user_role)

# Export key classes and functions
__all__ = [
    "UserRole",
    "Permission", 
    "PermissionsMatrix",
    "AccessControl",
    "access_control",
    "check_access",
    "has_permission", 
    "generate_user_menu",
    "UserContext"
]

# Simple UserContext class for compatibility
class UserContext:
    """Simple user context for background jobs and admin functions"""
    def __init__(self, user_id: int, org_id: int, role: str = "user"):
        self.user_id = user_id
        self.org_id = org_id
        self.role = role
        
    def has_permission(self, permission: str) -> bool:
        """Check if user has permission"""
        # Simple admin check
        return self.role == "admin"