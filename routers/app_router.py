"""
App Router Structure - Organized Route Management with RBAC Integration
Separates public and authenticated routes with role-based access control
"""

from typing import Dict, List, Optional, Any, Callable
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from enum import Enum
from dataclasses import dataclass
import logging

from lib.permissions import UserRole, Permission, AccessControl, PermissionsMatrix
from middleware.rbac import enforce_endpoint, get_current_user

logger = logging.getLogger(__name__)

class RouteGroup(Enum):
    """Route group categories"""
    PUBLIC = "public"           # No authentication required
    APP = "app"                # Authentication required
    API = "api"                # API endpoints
    ADMIN = "admin"            # Admin-only routes

@dataclass
class RouteConfig:
    """Configuration for a route"""
    path: str
    name: str
    title: str
    description: str
    group: RouteGroup
    required_permissions: List[Permission]
    required_roles: List[UserRole]
    template: Optional[str] = None
    icon: Optional[str] = None
    nav_category: Optional[str] = None
    nav_order: int = 0
    is_nav_item: bool = True

class RouteRegistry:
    """Registry for all application routes"""
    
    def __init__(self):
        self.routes: Dict[str, RouteConfig] = {}
        self.routers: Dict[RouteGroup, APIRouter] = {}
        self.access_control = AccessControl()
        self._initialize_routes()
        self._create_routers()
    
    def _initialize_routes(self):
        """Initialize all route configurations"""
        
        # Public routes (no authentication)
        public_routes = [
            RouteConfig(
                path="/",
                name="landing",
                title="Domus Conveyancing",
                description="Professional Planning Intelligence Platform",
                group=RouteGroup.PUBLIC,
                required_permissions=[],
                required_roles=[],
                template="index.html",
                is_nav_item=False
            ),
            RouteConfig(
                path="/login",
                name="login",
                title="Login",
                description="User authentication",
                group=RouteGroup.PUBLIC,
                required_permissions=[],
                required_roles=[],
                template="auth/login.html",
                is_nav_item=False
            ),
            RouteConfig(
                path="/register",
                name="register", 
                title="Register",
                description="Create new account",
                group=RouteGroup.PUBLIC,
                required_permissions=[],
                required_roles=[],
                template="auth/register.html",
                is_nav_item=False
            ),
            RouteConfig(
                path="/pricing",
                name="pricing",
                title="Pricing",
                description="Subscription plans and pricing",
                group=RouteGroup.PUBLIC,
                required_permissions=[],
                required_roles=[],
                template="public/pricing.html",
                is_nav_item=False
            )
        ]
        
        # Authenticated app routes
        app_routes = [
            # Dashboard
            RouteConfig(
                path="/app/dashboard",
                name="dashboard",
                title="Dashboard",
                description="Main dashboard overview",
                group=RouteGroup.APP,
                required_permissions=[Permission.VIEW_PROJECTS],
                required_roles=[UserRole.DEV, UserRole.CON, UserRole.OWN, UserRole.AUTH, UserRole.ADM],
                template="app/dashboard.html",
                icon="dashboard",
                nav_category="Overview",
                nav_order=1
            ),
            
            # Projects
            RouteConfig(
                path="/app/projects",
                name="projects",
                title="Projects",
                description="Project management and overview",
                group=RouteGroup.APP,
                required_permissions=[Permission.VIEW_PROJECTS],
                required_roles=[UserRole.DEV, UserRole.CON, UserRole.OWN, UserRole.ADM],
                template="app/projects.html",
                icon="folder",
                nav_category="Core",
                nav_order=2
            ),
            RouteConfig(
                path="/app/projects/new",
                name="projects_new",
                title="New Project",
                description="Create new project",
                group=RouteGroup.APP,
                required_permissions=[Permission.CREATE_PROJECTS],
                required_roles=[UserRole.DEV, UserRole.CON, UserRole.OWN, UserRole.ADM],
                template="app/projects_new.html",
                is_nav_item=False
            ),
            
            # Planning AI
            RouteConfig(
                path="/app/planning-ai",
                name="planning_ai",
                title="Planning AI",
                description="AI-powered planning analysis",
                group=RouteGroup.APP,
                required_permissions=[Permission.USE_PLANNING_AI],
                required_roles=[UserRole.DEV, UserRole.CON, UserRole.ADM],
                template="app/planning_ai.html",
                icon="brain",
                nav_category="AI Tools",
                nav_order=3
            ),
            
            # Development Calculator (New Module)
            RouteConfig(
                path="/app/development-calculator",
                name="development_calculator",
                title="Development Calculator",
                description="Financial viability and ROI analysis",
                group=RouteGroup.APP,
                required_permissions=[Permission.USE_VIABILITY_CALC],
                required_roles=[UserRole.DEV, UserRole.CON, UserRole.ADM],
                template="app/development_calculator.html",
                icon="calculator",
                nav_category="AI Tools",
                nav_order=4
            ),
            
            # Scheme Optimiser (New Module)
            RouteConfig(
                path="/app/scheme-optimiser",
                name="scheme_optimiser",
                title="Scheme Optimiser",
                description="Optimise schemes for planning and profit",
                group=RouteGroup.APP,
                required_permissions=[Permission.USE_SCHEME_OPTIMISER],
                required_roles=[UserRole.DEV, UserRole.CON, UserRole.ADM],
                template="app/scheme_optimiser.html",
                icon="target",
                nav_category="AI Tools",
                nav_order=5
            ),
            
            # Legislation Tracker (New Module)
            RouteConfig(
                path="/app/legislation-tracker",
                name="legislation_tracker",
                title="Legislation Tracker",
                description="Monitor planning law changes",
                group=RouteGroup.APP,
                required_permissions=[Permission.USE_LEGISLATION_TRACKER],
                required_roles=[UserRole.DEV, UserRole.CON, UserRole.AUTH, UserRole.ADM],
                template="app/legislation_tracker.html",
                icon="book",
                nav_category="Intelligence",
                nav_order=6
            ),
            
            # Planning Copilot (New Module)
            RouteConfig(
                path="/app/planning-copilot",
                name="planning_copilot",
                title="Planning Copilot",
                description="AI planning assistant and guidance",
                group=RouteGroup.APP,
                required_permissions=[Permission.USE_PLANNING_COPILOT],
                required_roles=[UserRole.DEV, UserRole.CON, UserRole.ADM],
                template="app/planning_copilot.html",
                icon="robot",
                nav_category="AI Tools",
                nav_order=7
            ),
            
            # Submit to Council (New Module)
            RouteConfig(
                path="/app/submit-to-council",
                name="submit_to_council",
                title="Submit to Council",
                description="Automated planning application submission",
                group=RouteGroup.APP,
                required_permissions=[Permission.SUBMIT_TO_COUNCIL],
                required_roles=[UserRole.DEV, UserRole.CON, UserRole.ADM],
                template="app/submit_to_council.html",
                icon="send",
                nav_category="Workflow",
                nav_order=8
            ),
            
            # Documents
            RouteConfig(
                path="/app/documents",
                name="documents",
                title="Auto-Docs",
                description="Professional document generation",
                group=RouteGroup.APP,
                required_permissions=[Permission.VIEW_DOCS],
                required_roles=[UserRole.DEV, UserRole.CON, UserRole.OWN, UserRole.ADM],
                template="app/auto_docs.html",
                icon="document",
                nav_category="Core",
                nav_order=9
            ),
            
            # Property API
            RouteConfig(
                path="/app/property-api",
                name="property_api",
                title="Property API",
                description="UK property data integration",
                group=RouteGroup.APP,
                required_permissions=[Permission.VIEW_PROPERTY_DATA],
                required_roles=[UserRole.DEV, UserRole.CON, UserRole.OWN, UserRole.ADM],
                template="app/property_api.html",
                icon="map",
                nav_category="Data",
                nav_order=10
            ),
            
            # Marketplace
            RouteConfig(
                path="/app/marketplace",
                name="marketplace",
                title="BNG Marketplace",
                description="Biodiversity Net Gain trading",
                group=RouteGroup.APP,
                required_permissions=[Permission.VIEW_MARKETPLACE_DEMAND],
                required_roles=[UserRole.DEV, UserRole.CON, UserRole.OWN, UserRole.ADM],
                template="app/offsets_marketplace.html",
                icon="leaf",
                nav_category="Marketplace",
                nav_order=11
            ),
            
            # Authority Portal
            RouteConfig(
                path="/app/authority-portal",
                name="authority_portal",
                title="Authority Portal",
                description="Planning authority dashboard",
                group=RouteGroup.APP,
                required_permissions=[Permission.ACCESS_AUTHORITY_PORTAL],
                required_roles=[UserRole.AUTH, UserRole.ADM],
                template="app/authority_portal.html",
                icon="shield",
                nav_category="Authority",
                nav_order=12
            ),
            
            # Settings
            RouteConfig(
                path="/app/settings",
                name="settings",
                title="Settings",
                description="Account and billing settings",
                group=RouteGroup.APP,
                required_permissions=[Permission.VIEW_PROFILE],
                required_roles=[UserRole.DEV, UserRole.CON, UserRole.OWN, UserRole.AUTH, UserRole.ADM],
                template="app/settings.html",
                icon="settings",
                nav_category="Account",
                nav_order=13
            ),
            RouteConfig(
                path="/app/billing",
                name="billing",
                title="Billing",
                description="Subscription and payment management",
                group=RouteGroup.APP,
                required_permissions=[Permission.VIEW_BILLING],
                required_roles=[UserRole.DEV, UserRole.CON, UserRole.OWN, UserRole.AUTH, UserRole.ADM],
                template="app/billing.html",
                icon="credit-card",
                nav_category="Account",
                nav_order=14
            )
        ]
        
        # Admin routes
        admin_routes = [
            RouteConfig(
                path="/admin/dashboard",
                name="admin_dashboard",
                title="Admin Dashboard",
                description="System administration overview",
                group=RouteGroup.ADMIN,
                required_permissions=[Permission.ADMIN_ACCESS],
                required_roles=[UserRole.ADM],
                template="admin/dashboard.html",
                icon="admin-panel",
                nav_category="Admin",
                nav_order=1
            ),
            RouteConfig(
                path="/admin/users",
                name="admin_users",
                title="User Management", 
                description="Manage users and organizations",
                group=RouteGroup.ADMIN,
                required_permissions=[Permission.MANAGE_USERS],
                required_roles=[UserRole.ADM],
                template="admin/users.html",
                icon="users",
                nav_category="Admin",
                nav_order=2
            ),
            RouteConfig(
                path="/admin/system",
                name="admin_system",
                title="System Health",
                description="System monitoring and health checks",
                group=RouteGroup.ADMIN,
                required_permissions=[Permission.ADMIN_ACCESS],
                required_roles=[UserRole.ADM],
                template="admin/system.html",
                icon="activity",
                nav_category="Admin",
                nav_order=3
            )
        ]
        
        # Register all routes
        all_routes = public_routes + app_routes + admin_routes
        for route in all_routes:
            self.routes[route.name] = route
    
    def _create_routers(self):
        """Create FastAPI routers for each route group"""
        
        for group in RouteGroup:
            self.routers[group] = APIRouter(
                prefix=f"/{group.value}" if group != RouteGroup.PUBLIC else "",
                tags=[group.value.title()]
            )
    
    def get_routes_for_group(self, group: RouteGroup) -> List[RouteConfig]:
        """Get all routes for a specific group"""
        return [route for route in self.routes.values() if route.group == group]
    
    def get_navigation_for_user(self, user_role: UserRole) -> Dict[str, List[Dict[str, Any]]]:
        """Generate navigation menu for user based on their role"""
        
        nav_items = {}
        
        for route in self.routes.values():
            # Skip non-navigation items
            if not route.is_nav_item:
                continue
            
            # Check if user has access to this route
            if not self.access_control.has_route_access(user_role, route.path):
                continue
            
            # Check role permissions
            if route.required_roles and user_role not in route.required_roles:
                continue
            
            # Add to navigation
            category = route.nav_category or "Other"
            if category not in nav_items:
                nav_items[category] = []
            
            nav_items[category].append({
                "name": route.name,
                "title": route.title,
                "path": route.path,
                "icon": route.icon,
                "description": route.description,
                "order": route.nav_order
            })
        
        # Sort items within each category
        for category in nav_items:
            nav_items[category].sort(key=lambda x: x["order"])
        
        return nav_items
    
    def get_route_config(self, route_name: str) -> Optional[RouteConfig]:
        """Get configuration for a specific route"""
        return self.routes.get(route_name)
    
    def has_access(self, user_role: UserRole, route_name: str) -> bool:
        """Check if user has access to a route"""
        route = self.get_route_config(route_name)
        if not route:
            return False
        
        # Check role requirements
        if route.required_roles and user_role not in route.required_roles:
            return False
        
        # Check permission requirements using AccessControl
        for permission in route.required_permissions:
            if not self.access_control.has_permission(user_role, permission):
                return False
        
        return True

class AppRouterManager:
    """Main router manager that integrates with FastAPI application"""
    
    def __init__(self, templates: Jinja2Templates):
        self.registry = RouteRegistry()
        self.templates = templates
        
    def setup_routes(self, app):
        """Setup all routes in the FastAPI application"""
        
        # Setup public routes
        self._setup_public_routes(app)
        
        # Setup authenticated app routes
        self._setup_app_routes(app)
        
        # Setup admin routes
        self._setup_admin_routes(app)
        
        # Setup API routes
        self._setup_api_routes(app)
    
    def _setup_public_routes(self, app):
        """Setup public routes (no authentication required)"""
        
        public_router = self.registry.routers[RouteGroup.PUBLIC]
        
        @public_router.get("/", response_class=HTMLResponse)
        async def landing_page(request: Request):
            return self.templates.TemplateResponse("index.html", {
                "request": request,
                "title": "Domus Conveyancing - Professional Planning Intelligence"
            })
        
        @public_router.get("/pricing", response_class=HTMLResponse) 
        async def pricing_page(request: Request):
            from lib.pricing import PricingConfig
            
            config = PricingConfig()
            return self.templates.TemplateResponse("public/pricing.html", {
                "request": request,
                "title": "Pricing - Domus Conveyancing",
                "pricing": config.get_all_plans()
            })
        
        @public_router.get("/login", response_class=HTMLResponse)
        async def login_page(request: Request):
            return self.templates.TemplateResponse("auth/login.html", {
                "request": request,
                "title": "Login - Domus Conveyancing"
            })
        
        @public_router.get("/register", response_class=HTMLResponse)
        async def register_page(request: Request):
            return self.templates.TemplateResponse("auth/register.html", {
                "request": request,
                "title": "Register - Domus Conveyancing"
            })
        
        app.include_router(public_router)
    
    def _setup_app_routes(self, app):
        """Setup authenticated application routes"""
        
        app_router = self.registry.routers[RouteGroup.APP]
        
        @app_router.get("/dashboard", response_class=HTMLResponse)
        @enforce_endpoint([Permission.VIEW_PROJECTS])
        async def dashboard(request: Request, current_user=Depends(get_current_user)):
            nav_items = self.registry.get_navigation_for_user(current_user.role)
            
            return self.templates.TemplateResponse("app/dashboard.html", {
                "request": request,
                "current_user": current_user,
                "nav_items": nav_items,
                "title": "Dashboard"
            })
        
        @app_router.get("/projects", response_class=HTMLResponse)
        @enforce_endpoint([Permission.VIEW_PROJECTS])
        async def projects(request: Request, current_user=Depends(get_current_user)):
            nav_items = self.registry.get_navigation_for_user(current_user.role)
            
            return self.templates.TemplateResponse("app/projects.html", {
                "request": request,
                "current_user": current_user,
                "nav_items": nav_items,
                "title": "Projects"
            })
        
        @app_router.get("/development-calculator", response_class=HTMLResponse)
        @enforce_endpoint([Permission.USE_VIABILITY_CALC])
        async def development_calculator(request: Request, current_user=Depends(get_current_user)):
            nav_items = self.registry.get_navigation_for_user(current_user.role)
            
            return self.templates.TemplateResponse("app/development_calculator.html", {
                "request": request,
                "current_user": current_user,
                "nav_items": nav_items,
                "title": "Development Calculator"
            })
        
        @app_router.get("/scheme-optimiser", response_class=HTMLResponse)
        @enforce_endpoint([Permission.USE_SCHEME_OPTIMISER])
        async def scheme_optimiser(request: Request, current_user=Depends(get_current_user)):
            nav_items = self.registry.get_navigation_for_user(current_user.role)
            
            return self.templates.TemplateResponse("app/scheme_optimiser.html", {
                "request": request,
                "current_user": current_user,
                "nav_items": nav_items,
                "title": "Scheme Optimiser"
            })
        
        @app_router.get("/legislation-tracker", response_class=HTMLResponse)
        @enforce_endpoint([Permission.USE_LEGISLATION_TRACKER])
        async def legislation_tracker(request: Request, current_user=Depends(get_current_user)):
            nav_items = self.registry.get_navigation_for_user(current_user.role)
            
            return self.templates.TemplateResponse("app/legislation_tracker.html", {
                "request": request,
                "current_user": current_user,
                "nav_items": nav_items,
                "title": "Legislation Tracker"
            })
        
        @app_router.get("/planning-copilot", response_class=HTMLResponse)
        @enforce_endpoint([Permission.USE_PLANNING_COPILOT])
        async def planning_copilot(request: Request, current_user=Depends(get_current_user)):
            nav_items = self.registry.get_navigation_for_user(current_user.role)
            
            return self.templates.TemplateResponse("app/planning_copilot.html", {
                "request": request,
                "current_user": current_user,
                "nav_items": nav_items,
                "title": "Planning Copilot"
            })
        
        @app_router.get("/submit-to-council", response_class=HTMLResponse)
        @enforce_endpoint([Permission.SUBMIT_TO_COUNCIL])
        async def submit_to_council(request: Request, current_user=Depends(get_current_user)):
            nav_items = self.registry.get_navigation_for_user(current_user.role)
            
            return self.templates.TemplateResponse("app/submit_to_council.html", {
                "request": request,
                "current_user": current_user,
                "nav_items": nav_items,
                "title": "Submit to Council"
            })
        
        # Add other app routes following the same pattern...
        
        app.include_router(app_router)
    
    def _setup_admin_routes(self, app):
        """Setup admin-only routes"""
        
        admin_router = self.registry.routers[RouteGroup.ADMIN]
        
        @admin_router.get("/dashboard", response_class=HTMLResponse)
        @enforce_endpoint([Permission.ADMIN_ACCESS])
        async def admin_dashboard(request: Request, current_user=Depends(get_current_user)):
            nav_items = self.registry.get_navigation_for_user(current_user.role)
            
            return self.templates.TemplateResponse("admin/dashboard.html", {
                "request": request,
                "current_user": current_user,
                "nav_items": nav_items,
                "title": "Admin Dashboard"
            })
        
        @admin_router.get("/system", response_class=HTMLResponse)
        @enforce_endpoint([Permission.ADMIN_ACCESS])
        async def admin_system(request: Request, current_user=Depends(get_current_user)):
            # Run health check
            from modules.health_check import health_check_runner
            
            try:
                report = await health_check_runner.run_full_health_check()
                health_status = {
                    "status": report.overall_status,
                    "total_checks": report.total_checks,
                    "failed_checks": report.failed_checks,
                    "critical_issues": report.critical_issues,
                    "production_ready": report.is_production_ready
                }
            except Exception as e:
                health_status = {
                    "status": "error",
                    "error": str(e),
                    "production_ready": False
                }
            
            nav_items = self.registry.get_navigation_for_user(current_user.role)
            
            return self.templates.TemplateResponse("admin/system.html", {
                "request": request,
                "current_user": current_user,
                "nav_items": nav_items,
                "health_status": health_status,
                "title": "System Health"
            })
        
        app.include_router(admin_router)
    
    def _setup_api_routes(self, app):
        """Setup API routes for the new modules"""
        
        api_router = APIRouter(prefix="/api/v1", tags=["API"])
        
        # Development Calculator API
        @api_router.post("/development-calculator/calculate")
        @enforce_endpoint([Permission.USE_VIABILITY_CALC])
        async def calculate_viability(request: Request, current_user=Depends(get_current_user)):
            from modules.development_calculator import development_calculator
            
            # This would implement the actual API endpoint
            return {"message": "Development calculator API endpoint"}
        
        # Scheme Optimiser API
        @api_router.post("/scheme-optimiser/optimise")
        @enforce_endpoint([Permission.USE_SCHEME_OPTIMISER])
        async def optimise_scheme(request: Request, current_user=Depends(get_current_user)):
            from modules.scheme_optimiser import scheme_optimiser
            
            # This would implement the actual API endpoint
            return {"message": "Scheme optimiser API endpoint"}
        
        # Legislation Tracker API
        @api_router.get("/legislation-tracker/impacts/{project_id}")
        @enforce_endpoint([Permission.USE_LEGISLATION_TRACKER])
        async def get_legislation_impacts(project_id: str, current_user=Depends(get_current_user)):
            from modules.legislation_tracker import legislation_tracker
            
            # This would implement the actual API endpoint
            return {"message": f"Legislation impacts for project {project_id}"}
        
        # Planning Copilot API
        @api_router.post("/planning-copilot/ask")
        @enforce_endpoint([Permission.USE_PLANNING_COPILOT])
        async def ask_planning_copilot(request: Request, current_user=Depends(get_current_user)):
            from modules.planning_copilot import planning_copilot
            
            # This would implement the actual API endpoint
            return {"message": "Planning copilot API endpoint"}
        
        # Submit to Council API
        @api_router.post("/submit-to-council/submit")
        @enforce_endpoint([Permission.SUBMIT_TO_COUNCIL])
        async def submit_to_council_api(request: Request, current_user=Depends(get_current_user)):
            from modules.submit_to_council import submission_tracker
            
            # This would implement the actual API endpoint
            return {"message": "Submit to council API endpoint"}
        
        # Health Check API
        @api_router.get("/health-check/run")
        @enforce_endpoint([Permission.ADMIN_ACCESS])
        async def run_health_check_api(current_user=Depends(get_current_user)):
            from modules.health_check import health_check_runner
            
            try:
                report = await health_check_runner.run_full_health_check()
                return {
                    "status": report.overall_status,
                    "total_checks": report.total_checks,
                    "passed_checks": report.passed_checks,
                    "failed_checks": report.failed_checks,
                    "critical_issues": report.critical_issues,
                    "production_ready": report.is_production_ready,
                    "summary": report.summary
                }
            except Exception as e:
                return {"error": str(e), "status": "error"}
        
        app.include_router(api_router)
    
    def get_navigation_for_user(self, user_role: UserRole) -> Dict[str, List[Dict[str, Any]]]:
        """Get navigation items for user"""
        return self.registry.get_navigation_for_user(user_role)

# Global router manager instance
router_manager = None

def initialize_router_manager(templates: Jinja2Templates) -> AppRouterManager:
    """Initialize the router manager"""
    global router_manager
    router_manager = AppRouterManager(templates)
    return router_manager

def get_router_manager() -> AppRouterManager:
    """Get the router manager instance"""
    global router_manager
    if router_manager is None:
        raise RuntimeError("Router manager not initialized")
    return router_manager

# Export classes and functions
__all__ = [
    "RouteGroup",
    "RouteConfig", 
    "RouteRegistry",
    "AppRouterManager",
    "initialize_router_manager",
    "get_router_manager"
]