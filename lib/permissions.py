""""""

Role-Based Access Control (RBAC) system for DomusRole-Based Access Control (RBAC) system for Domus

Server-side permissions enforcement with org scopingServer-side permissions enforcement with org scoping

""""""



from typing import Dict, List, Tuple, Optionalfrom typing import Dict, List, Tuple, Optional

from fastapi import HTTPException, Depends, Request, statusfrom fastapi import HTTPException, Depends, Request, status

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentialsfrom fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy.orm import Sessionfrom sqlalchemy.orm import Session

from database_config import get_dbfrom database_config import get_db

from models import User, Organization, Membershipfrom models import User, Organization, Membership

import jwtimport jwt

import osimport os



# Security scheme# Security scheme

security = HTTPBearer(auto_error=False)security = HTTPBearer(auto_error=False)



# Role definitions and permissions mapping# Role definitions and permissions mapping

ROLE_PERMISSIONS: Dict[str, List[str]] = {ROLE_PERMISSIONS: Dict[str, List[str]] = {

    "Owner": [    "Owner": [

        "org:read", "org:write", "org:transfer",        "org:read", "org:write", "org:transfer",

        "users:read", "users:invite", "users:role:set",        "users:read", "users:invite", "users:role:set",

        "roles:read", "roles:write",        "roles:read", "roles:write",

        "cases:read", "cases:write", "cases:assign",        "cases:read", "cases:write", "cases:assign",

        "documents:read", "documents:write",        "documents:read", "documents:write",

        "billing:read", "billing:manage",        "billing:read", "billing:manage",

        "enterprise:read",        "enterprise:read",

        "audit:read"        "audit:read"

    ],    ],

    "Admin": [    "Admin": [

        "org:read", "org:write",        "org:read", "org:write",

        "users:read", "users:invite", "users:role:set",        "users:read", "users:invite", "users:role:set",

        "roles:read", "roles:write",        "roles:read", "roles:write",

        "cases:read", "cases:write", "cases:assign",        "cases:read", "cases:write", "cases:assign",

        "documents:read", "documents:write",        "documents:read", "documents:write",

        "billing:read", "billing:manage",        "billing:read", "billing:manage",

        "enterprise:read",        "enterprise:read",

        "audit:read"        "audit:read"

    ],    ],

    "Manager": [    "Manager": [

        "org:read",        "org:read",

        "users:read",        "users:read",

        "cases:read", "cases:write", "cases:assign",        "cases:read", "cases:write", "cases:assign",

        "documents:read", "documents:write",        "documents:read", "documents:write",

        "enterprise:read",        "enterprise:read",

        "audit:read"        "audit:read"

    ],    ],

    "Staff": [    "Staff": [

        "org:read",        "org:read",

        "cases:read", "cases:write",  # Scoped to assigned cases only        "cases:read", "cases:write",  # Scoped to assigned cases only

        "documents:read", "documents:write"  # Scoped to assigned cases only        "documents:read", "documents:write"  # Scoped to assigned cases only

    ],    ],

    "BillingOnly": [    "BillingOnly": [

        "billing:read", "billing:manage"        "billing:read", "billing:manage"

    ],    ],

    "ReadOnly": [    "ReadOnly": [

        "org:read",        "org:read",

        "cases:read",        "cases:read",

        "documents:read",        "documents:read",

        "enterprise:read",        "enterprise:read",

        "audit:read"        "audit:read"

    ],    ],

    "Client": [    "Client": [

        "cases:read",  # Scoped to own cases only        "cases:read",  # Scoped to own cases only

        "documents:read"  # Scoped to own cases only        "documents:read"  # Scoped to own cases only

    ]    ]

}}



class AuthContext:class AuthContext:

    """Authentication context containing user, org, and membership info"""    """Authentication context containing user, org, and membership info"""

    def __init__(self, user: User, org: Organization, membership: Membership):    def __init__(self, user: User, org: Organization, membership: Membership):

        self.user = user        self.user = user

        self.org = org        self.org = org

        self.membership = membership        self.membership = membership

        self.role = membership.role        self.role = membership.role

        self.permissions = ROLE_PERMISSIONS.get(self.role, [])        self.permissions = ROLE_PERMISSIONS.get(self.role, [])

    VIEW_AI_ANALYSIS = "view_ai_analysis"

def get_current_user_from_token(token: str, db: Session) -> Optional[User]:    EXPORT_AI_ANALYSIS = "export_ai_analysis"

    """Extract user from JWT token"""    

    try:    # Documents

        # Replace with your JWT secret from environment    GENERATE_DOCS = "generate_docs"

        secret = os.getenv("JWT_SECRET", "your-secret-key")    VIEW_DOCS = "view_docs"

        payload = jwt.decode(token, secret, algorithms=["HS256"])    EDIT_DOCS = "edit_docs"

        user_id = payload.get("sub")    DELETE_DOCS = "delete_docs"

            GENERATE_ADVANCED_DOCS = "generate_advanced_docs"

        if user_id is None:    

            return None    # Submission packs

                CREATE_SUBMISSION_PACK = "create_submission_pack"

        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()    VIEW_SUBMISSION_PACK = "view_submission_pack"

        return user    EDIT_SUBMISSION_PACK = "edit_submission_pack"

    except jwt.PyJWTError:    SUBMIT_TO_COUNCIL = "submit_to_council"

        return None    

    # Marketplace

def get_user_org_membership(user: User, org_slug: str, db: Session) -> Optional[Tuple[Organization, Membership]]:    VIEW_MARKETPLACE_DEMAND = "view_marketplace_demand"

    """Get user's organization and membership"""    CREATE_MARKETPLACE_DEMAND = "create_marketplace_demand"

    org = db.query(Organization).filter(Organization.slug == org_slug).first()    VIEW_MARKETPLACE_SUPPLY = "view_marketplace_supply"

    if not org:    CREATE_MARKETPLACE_SUPPLY = "create_marketplace_supply"

        return None    MANAGE_MARKETPLACE_LISTINGS = "manage_marketplace_listings"

            

    membership = db.query(Membership).filter(    # Contracts

        Membership.user_id == user.id,    VIEW_CONTRACTS = "view_contracts"

        Membership.org_id == org.id    CREATE_CONTRACTS = "create_contracts"

    ).first()    EDIT_CONTRACTS = "edit_contracts"

        SIGN_CONTRACTS = "sign_contracts"

    if not membership:    

        return None    # Analytics

            VIEW_BASIC_ANALYTICS = "view_basic_analytics"

    return org, membership    VIEW_FULL_ANALYTICS = "view_full_analytics"

    VIEW_LPA_ANALYTICS = "view_lpa_analytics"

async def require_auth(    VIEW_ORG_INSIGHTS = "view_org_insights"

    request: Request,    

    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),    # Appeals & Objections

    db: Session = Depends(get_db)    VIEW_APPEALS = "view_appeals"

) -> AuthContext:    CREATE_APPEALS = "create_appeals"

    """    VIEW_OBJECTIONS = "view_objections"

    Require authentication and return auth context    ANALYZE_OBJECTIONS = "analyze_objections"

    Returns (user, org, membership) or raises 401    

    """    # New Premium Modules

    # Try to get token from Authorization header or cookies    USE_VIABILITY_CALC = "use_viability_calc"

    token = None    USE_SCHEME_OPTIMISER = "use_scheme_optimiser"

    if credentials:    USE_LEGISLATION_TRACKER = "use_legislation_tracker"

        token = credentials.credentials    USE_PLANNING_COPILOT = "use_planning_copilot"

    elif "session_token" in request.cookies:    ACCESS_PREMIUM_MODULES = "access_premium_modules"

        token = request.cookies["session_token"]    ACCESS_APP_FEATURES = "access_app_features"

        

    if not token:    # General access permissions

        raise HTTPException(    VIEW_PROFILE = "view_profile"

            status_code=status.HTTP_401_UNAUTHORIZED,    VIEW_BILLING = "view_billing"

            detail="Authentication required"    VIEW_PROPERTY_DATA = "view_property_data"

        )    ACCESS_AUTHORITY_PORTAL = "access_authority_portal"

        ADMIN_ACCESS = "admin_access"

    # Get user from token    

    user = get_current_user_from_token(token, db)    # Settings & Admin

    if not user:    VIEW_SETTINGS = "view_settings"

        raise HTTPException(    EDIT_SETTINGS = "edit_settings"

            status_code=status.HTTP_401_UNAUTHORIZED,    MANAGE_BILLING = "manage_billing"

            detail="Invalid or expired token"    MANAGE_CREDITS = "manage_credits"

        )    MANAGE_SECURITY = "manage_security"

        

    # Get organization from URL path or default to first membership    # Authority access

    org_slug = None    VIEW_AUTHORITY_PORTAL = "view_authority_portal"

    path_parts = request.url.path.strip("/").split("/")    COMMENT_ON_SUBMISSIONS = "comment_on_submissions"

        

    # Try to extract org slug from URL patterns like /org/{slug}/...    # Admin functions

    if len(path_parts) >= 2 and path_parts[0] == "org":    MANAGE_USERS = "manage_users"

        org_slug = path_parts[1]    MANAGE_ORGANIZATIONS = "manage_organizations"

        VIEW_SYSTEM_LOGS = "view_system_logs"

    # If no org in URL, use the user's first active membership    MANAGE_SYSTEM_CONFIG = "manage_system_config"

    if not org_slug:

        membership = db.query(Membership).filter(Membership.user_id == user.id).first()@dataclass

        if not membership:class RolePermissions:

            raise HTTPException(    """Permissions assigned to a role"""

                status_code=status.HTTP_403_FORBIDDEN,    role: UserRole

                detail="No organization access"    permissions: Set[Permission]

            )    description: str

        org = db.query(Organization).filter(Organization.id == membership.org_id).first()

    else:class PermissionsMatrix:

        # Get specific org and membership    """Central permissions matrix - single source of truth"""

        result = get_user_org_membership(user, org_slug, db)    

        if not result:    ROLE_PERMISSIONS = {

            raise HTTPException(        UserRole.DEV: RolePermissions(

                status_code=status.HTTP_403_FORBIDDEN,            role=UserRole.DEV,

                detail="No access to this organization"            permissions={

            )                # Projects

        org, membership = result                Permission.VIEW_PROJECTS,

                    Permission.CREATE_PROJECTS,

    return AuthContext(user, org, membership)                Permission.EDIT_PROJECTS,

                Permission.DELETE_PROJECTS,

def require_permission(permission: str):                

    """                # Planning AI

    FastAPI dependency to require specific permission                Permission.USE_PLANNING_AI,

    Usage: @router.get("/endpoint", dependencies=[Depends(require_permission("cases:read"))])                Permission.VIEW_AI_ANALYSIS,

    """                Permission.EXPORT_AI_ANALYSIS,

    async def permission_dependency(auth_ctx: AuthContext = Depends(require_auth)) -> AuthContext:                

        if permission not in auth_ctx.permissions:                # Documents (basic)

            raise HTTPException(                Permission.GENERATE_DOCS,

                status_code=status.HTTP_403_FORBIDDEN,                Permission.VIEW_DOCS,

                detail=f"Permission '{permission}' required"                Permission.EDIT_DOCS,

            )                Permission.DELETE_DOCS,

        return auth_ctx                

                    # Submission packs

    return permission_dependency                Permission.CREATE_SUBMISSION_PACK,

                Permission.VIEW_SUBMISSION_PACK,

def apply_org_scoping(query, model, auth_ctx: AuthContext):                Permission.EDIT_SUBMISSION_PACK,

    """Apply organization scoping to SQLAlchemy query"""                Permission.SUBMIT_TO_COUNCIL,

    if hasattr(model, 'org_id'):                

        return query.filter(model.org_id == auth_ctx.org.id)                # Marketplace (demand side)

    return query                Permission.VIEW_MARKETPLACE_DEMAND,

                Permission.CREATE_MARKETPLACE_DEMAND,

def apply_staff_scoping(query, model, auth_ctx: AuthContext):                

    """Apply staff scoping - only assigned cases/docs"""                # Contracts

    if auth_ctx.role == "Staff":                Permission.VIEW_CONTRACTS,

        if hasattr(model, 'assigned_to'):                Permission.CREATE_CONTRACTS,

            return query.filter(model.assigned_to == auth_ctx.user.id)                Permission.EDIT_CONTRACTS,

        elif hasattr(model, 'case_id'):                Permission.SIGN_CONTRACTS,

            # For documents, filter by cases assigned to staff                

            from models import Case                # Analytics (basic)

            assigned_case_ids = [c.id for c in query.session.query(Case).filter(                Permission.VIEW_BASIC_ANALYTICS,

                Case.org_id == auth_ctx.org.id,                

                Case.assigned_to == auth_ctx.user.id                # New Premium Modules

            ).all()]                Permission.USE_VIABILITY_CALC,

            return query.filter(model.case_id.in_(assigned_case_ids))                Permission.USE_SCHEME_OPTIMISER,

    return query                Permission.USE_PLANNING_COPILOT,

                

def apply_client_scoping(query, model, auth_ctx: AuthContext):                # General access

    """Apply client scoping - only own cases/docs"""                Permission.VIEW_PROFILE,

    if auth_ctx.role == "Client":                Permission.VIEW_BILLING,

        if hasattr(model, 'client_user_id'):                Permission.VIEW_PROPERTY_DATA,

            return query.filter(model.client_user_id == auth_ctx.user.id)                

        elif hasattr(model, 'case_id'):                # Settings

            # For documents, filter by client's own cases                Permission.VIEW_SETTINGS,

            from models import Case                Permission.EDIT_SETTINGS,

            client_case_ids = [c.id for c in query.session.query(Case).filter(                Permission.MANAGE_BILLING,

                Case.org_id == auth_ctx.org.id,                Permission.MANAGE_CREDITS,

                Case.client_user_id == auth_ctx.user.id                Permission.MANAGE_SECURITY

            ).all()]            },

            return query.filter(model.case_id.in_(client_case_ids))            description="Developer with project management and planning tools"

    return query        ),

        

def build_scoped_query(query, model, auth_ctx: AuthContext):        UserRole.CON: RolePermissions(

    """            role=UserRole.CON,

    Build a properly scoped query based on user role and permissions            permissions={

    Always applies org scoping, then role-specific scoping                # All DEV permissions plus...

    """                Permission.VIEW_PROJECTS,

    # Always apply org scoping                Permission.CREATE_PROJECTS,

    query = apply_org_scoping(query, model, auth_ctx)                Permission.EDIT_PROJECTS,

                    Permission.DELETE_PROJECTS,

    # Apply role-specific scoping                Permission.USE_PLANNING_AI,

    query = apply_staff_scoping(query, model, auth_ctx)                Permission.VIEW_AI_ANALYSIS,

    query = apply_client_scoping(query, model, auth_ctx)                Permission.EXPORT_AI_ANALYSIS,

                    Permission.GENERATE_DOCS,

    return query                Permission.VIEW_DOCS,

                Permission.EDIT_DOCS,

def has_permission(auth_ctx: AuthContext, permission: str) -> bool:                Permission.DELETE_DOCS,

    """Check if user has specific permission"""                Permission.CREATE_SUBMISSION_PACK,

    return permission in auth_ctx.permissions                Permission.VIEW_SUBMISSION_PACK,

                Permission.EDIT_SUBMISSION_PACK,

def can_access_user_management(auth_ctx: AuthContext) -> bool:                Permission.SUBMIT_TO_COUNCIL,

    """Check if user can access user management features"""                Permission.VIEW_MARKETPLACE_DEMAND,

    return auth_ctx.role in ["Owner", "Admin"]                Permission.CREATE_MARKETPLACE_DEMAND,

                Permission.VIEW_CONTRACTS,

def can_access_billing(auth_ctx: AuthContext) -> bool:                Permission.CREATE_CONTRACTS,

    """Check if user can access billing features"""                Permission.EDIT_CONTRACTS,

    return auth_ctx.role in ["Owner", "Admin", "BillingOnly"]                Permission.SIGN_CONTRACTS,

                Permission.VIEW_SETTINGS,

def can_access_enterprise(auth_ctx: AuthContext) -> bool:                Permission.EDIT_SETTINGS,

    """Check if user can access enterprise features"""                Permission.MANAGE_BILLING,

    return auth_ctx.role in ["Owner", "Admin", "Manager"]                Permission.MANAGE_CREDITS,
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

# Utility functions for compatibility
def has_feature_access(user_context: UserContext, feature: str) -> bool:
    """Check if user has access to a feature"""
    if not user_context:
        return False
    # Simple admin check for now
    return user_context.role == "admin"

def check_access(user_context: UserContext, permission: str) -> bool:
    """Check if user has a permission"""
    if not user_context:
        return False
    return user_context.has_permission(permission)

# Export compatibility aliases
Role = UserRole  # Alias for backward compatibility
Feature = Permission  # Alias for backward compatibility

# Export all public items
__all__ = [
    "UserRole", "Role", "Permission", "Feature", "PermissionsMatrix", 
    "AccessControl", "UserContext", "check_access", "has_feature_access"
]