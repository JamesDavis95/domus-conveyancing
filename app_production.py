"""
Production Domus Planning Platform
Complete integration of all production systems with comprehensive API endpoints
"""

from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from datetime import datetime
import os
import asyncio

# Import all production modules
from models import get_db, Base, User, Organization
from production_auth_complete import (
    get_current_user, require_role, require_quota, login_endpoint, 
    register_endpoint, get_me_endpoint, AuthService
)
from backend_auth_complete import UserRole, PlanType, has_permission
from stripe_integration_complete import StripeService, BillingAPI, WebhookHandler
from production_infrastructure import (
    MonitoringAPI, HealthCheckService, ErrorTrackingService,
    error_handling_middleware, scheduled_health_checks
)
from production_data_layer import (
    ProjectService, BNGMarketplaceService, LPAService, NotificationService,
    ProductionDataAPI
)
from client_onboarding import OnboardingService, OnboardingAPI, EmailService
from operational_admin_tools import (
    UserManagementService, SubscriptionManagementService,
    MarketplaceOversightService, SystemMonitoringService, AdminAPI
)

# Initialize FastAPI application
app = FastAPI(
    title="Domus Planning Platform - Production",
    description="Complete AI-powered planning intelligence system with BNG marketplace",
    version="4.0.0-production",
    contact={
        "name": "Domus Platform Support",
        "email": "support@domusplanning.co.uk",
        "url": "https://domusplanning.co.uk"
    },
    docs_url="/admin/docs",  # Restrict API docs to admin path
    redoc_url="/admin/redoc"
)

# CORS configuration for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://domus-conveyancing.onrender.com",
        "https://domusplanning.co.uk",
        "https://app.domusplanning.co.uk"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"]
)

# Add error handling middleware
app.middleware("http")(error_handling_middleware)

# Create database tables
engine = create_engine("sqlite:///./production.db", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)

# Serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Health check endpoints (public)
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Public health check endpoint"""
    return await MonitoringAPI.health_check(db)

@app.get("/")
async def root():
    """Serve main application"""
    with open("frontend/platform_clean.html", "r") as f:
        content = f.read()
    return HTMLResponse(content)

# Authentication endpoints
@app.post("/api/auth/login")
async def login(
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    """User login"""
    return await login_endpoint(email, password, db)

@app.post("/api/auth/register")
async def register(
    email: str,
    password: str,
    name: str,
    organization_name: str,
    role: str = "developer",
    plan_type: str = "core",
    db: Session = Depends(get_db)
):
    """User registration"""
    return await register_endpoint(
        email=email,
        password=password,
        name=name,
        organization_name=organization_name,
        role=UserRole(role),
        plan_type=PlanType(plan_type),
        db=db
    )

@app.get("/api/auth/me")
async def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user profile"""
    return get_me_endpoint(current_user, db)

# Onboarding endpoints
@app.post("/api/onboarding/start")
async def start_onboarding(
    email: str,
    referral_source: str = None,
    utm_campaign: str = None,
    utm_source: str = None,
    utm_medium: str = None,
    db: Session = Depends(get_db)
):
    """Start onboarding process"""
    return await OnboardingAPI.start_registration(
        email=email,
        referral_source=referral_source,
        utm_campaign=utm_campaign,
        utm_source=utm_source,
        utm_medium=utm_medium,
        db=db
    )

@app.get("/api/onboarding/plans")
async def get_plans():
    """Get available subscription plans"""
    return await OnboardingAPI.get_plan_options()

# Dashboard and data endpoints
@app.get("/api/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get real dashboard data"""
    return await ProductionDataAPI.get_dashboard_data(current_user, db)

@app.get("/api/projects")
async def get_projects(
    status: str = None,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user projects"""
    from production_data_layer import ProjectStatus
    status_enum = ProjectStatus(status) if status else None
    return await ProjectService.get_user_projects(current_user, status_enum, limit, offset, db)

@app.post("/api/projects")
async def create_project(
    project_data: dict,
    current_user: User = Depends(require_quota("site_analyses")),
    db: Session = Depends(get_db)
):
    """Create new project"""
    return await ProjectService.create_project(current_user, project_data, db)

@app.post("/api/planning/analyze")
async def analyze_site(
    site_address: str,
    development_details: dict,
    current_user: User = Depends(require_quota("site_analyses")),
    db: Session = Depends(get_db)
):
    """AI-powered site analysis"""
    return await ProjectService.analyze_site(current_user, site_address, development_details, db)

# BNG Marketplace endpoints
@app.get("/api/bng/listings")
async def search_bng_listings(
    habitat_type: str = None,
    max_price: float = None,
    location: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search BNG marketplace listings"""
    return await ProductionDataAPI.get_bng_marketplace_data(
        habitat_type=habitat_type,
        max_price=max_price,
        location=location,
        user=current_user,
        db=db
    )

@app.post("/api/bng/listings")
async def create_bng_listing(
    listing_data: dict,
    current_user: User = Depends(require_quota("bng_listings")),
    db: Session = Depends(get_db)
):
    """Create BNG listing"""
    return await BNGMarketplaceService.create_listing(current_user, listing_data, db)

@app.get("/api/bng/my-listings")
async def get_my_listings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get provider's BNG listings"""
    return await BNGMarketplaceService.get_provider_listings(current_user, db=db)

# LPA and statistics endpoints
@app.get("/api/lpa/stats")
async def get_lpa_stats(
    postcode: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get LPA statistics by postcode"""
    return await LPAService.get_lpa_by_postcode(postcode, db)

@app.get("/api/lpa/top-performing")
async def get_top_lpas(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get top performing LPAs"""
    return await LPAService.get_top_performing_lpas(limit, db)

@app.get("/api/lpa/challenging")
async def get_challenging_lpas(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get most challenging LPAs"""
    return await LPAService.get_challenging_lpas(limit, db)

# Notifications endpoints
@app.get("/api/notifications")
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user notifications"""
    return await NotificationService.get_user_notifications(current_user, unread_only, limit, db)

@app.patch("/api/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark notification as read"""
    success = await NotificationService.mark_notification_read(notification_id, current_user, db)
    if success:
        return {"message": "Notification marked as read"}
    raise HTTPException(status_code=404, detail="Notification not found")

# Billing endpoints
@app.get("/api/billing")
async def get_billing_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get billing information"""
    return await BillingAPI.get_billing_info(current_user, db)

@app.post("/api/billing/subscription")
async def create_subscription(
    plan_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create subscription"""
    return await BillingAPI.create_subscription(current_user, PlanType(plan_type), db)

@app.patch("/api/billing/subscription")
async def update_subscription(
    new_plan_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update subscription"""
    return await BillingAPI.update_subscription(current_user, PlanType(new_plan_type), db)

@app.post("/api/billing/portal")
async def get_billing_portal(
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """Get Stripe billing portal URL"""
    return_url = str(request.base_url) + "billing"
    portal_url = await StripeService.get_billing_portal_url(
        current_user.organization.stripe_customer_id,
        return_url
    )
    return {"portal_url": portal_url}

# Stripe webhooks
@app.post("/api/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Stripe webhooks"""
    return await WebhookHandler.handle_webhook(request, db)

# Admin endpoints (require admin role)
@app.get("/api/admin/dashboard")
async def admin_dashboard(
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Admin dashboard"""
    return await AdminAPI.get_dashboard(admin_user, db)

@app.get("/api/admin/users")
async def admin_get_users(
    search: str = None,
    role: str = None,
    plan_type: str = None,
    page: int = 1,
    per_page: int = 50,
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    role_enum = UserRole(role) if role else None
    plan_enum = PlanType(plan_type) if plan_type else None
    return await UserManagementService.get_all_users(
        search=search,
        role=role_enum,
        plan_type=plan_enum,
        page=page,
        per_page=per_page,
        db=db
    )

@app.get("/api/admin/users/{user_id}")
async def admin_get_user_details(
    user_id: int,
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get user details (admin only)"""
    return await UserManagementService.get_user_details(user_id, db)

@app.post("/api/admin/users/{user_id}/suspend")
async def admin_suspend_user(
    user_id: int,
    reason: str,
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Suspend user (admin only)"""
    return await UserManagementService.suspend_user(user_id, reason, admin_user, db)

@app.post("/api/admin/users/{user_id}/activate")
async def admin_activate_user(
    user_id: int,
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Activate user (admin only)"""
    return await UserManagementService.activate_user(user_id, admin_user, db)

@app.get("/api/admin/subscriptions")
async def admin_subscription_overview(
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Subscription overview (admin only)"""
    return await SubscriptionManagementService.get_subscription_overview(db)

@app.get("/api/admin/marketplace")
async def admin_marketplace_overview(
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Marketplace overview (admin only)"""
    return await MarketplaceOversightService.get_marketplace_overview(db)

@app.get("/api/admin/system/status")
async def admin_system_status(
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Detailed system status (admin only)"""
    return await MonitoringAPI.detailed_status(admin_user, db)

@app.get("/api/admin/analytics")
async def admin_analytics(
    days: int = 30,
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Platform analytics (admin only)"""
    return await SystemMonitoringService.get_platform_analytics(days, db)

@app.post("/api/admin/backup")
async def admin_create_backup(
    background_tasks: BackgroundTasks,
    admin_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Create manual backup (admin only)"""
    return await MonitoringAPI.create_manual_backup(background_tasks, admin_user)

# Super admin endpoints
@app.post("/api/admin/impersonate/{user_id}")
async def super_admin_impersonate(
    user_id: int,
    admin_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """Impersonate user (super admin only)"""
    return await AdminAPI.impersonate_user(user_id, admin_user, db)

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    await ErrorTrackingService.log_error(
        "http_exception",
        f"HTTP {exc.status_code}: {exc.detail}",
        request_path=str(request.url)
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    await ErrorTrackingService.log_error(
        "unhandled_exception",
        str(exc),
        request_path=str(request.url),
        stack_trace=str(exc)
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize background tasks and services"""
    
    # Start background health monitoring
    asyncio.create_task(scheduled_health_checks())
    
    # Log startup
    print("🚀 Domus Planning Platform - Production Started")
    print("   Version: 4.0.0-production")
    print("   Environment: Production")
    print("   Database: SQLite (production.db)")
    print("   Features: Authentication, Billing, Monitoring, BNG Marketplace")
    print("   Admin Panel: /admin/docs")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🔄 Domus Planning Platform - Graceful Shutdown")

if __name__ == "__main__":
    import uvicorn
    
    # Production server configuration
    uvicorn.run(
        "app_production:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info",
        access_log=True,
        reload=False  # Disable reload in production
    )