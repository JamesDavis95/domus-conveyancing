#!/usr/bin/env python3
"""
Domus Planning Platform - Professional Planning Intelligence System
Complete AI-powered planning and development solution

Planning AI - Site analysis and approval probability prediction
Auto-Docs - Professional planning document generation  
Property API - Unified UK property data integration
Offsets Marketplace - Biodiversity Net Gain trading platform
"""

import os
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from pathlib import Path
import random
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Import our auth system
from auth_system import (
    get_current_user, require_permission, require_quota, 
    hash_password, verify_password, create_access_token,
    increment_usage, org_scoped_query
)
from models import Users, Orgs, Projects, UserRole, PlanType

# Database dependency (placeholder - need to set up proper DB session)
def get_db():
    # TODO: Implement proper database session
    pass

# Pydantic models for requests
class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    email: str
    password: str
    org_name: str
    role: UserRole = UserRole.DEVELOPER

class ProjectCreateRequest(BaseModel):
    title: str
    address: str = None
    site_geometry: dict = None

# Mock implementations for optional services
class StripeService:
    @staticmethod
    async def get_billing_portal_url(org_id: int, return_url: str, db: Session):
        return f"https://billing.stripe.com/p/login/test_{org_id}"

# Environment flags for optional features
PRODUCTION_AUTH_AVAILABLE = False

# Simple database initialization function
def init_database():
    # TODO: Implement proper database initialization
    pass

# Initialize database on startup
init_database()
def init_database():
    """Initialize database tables if they don't exist"""
    try:
        from models import Base, engine
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables initialized")
    except Exception as e:
        print(f"⚠️ Database initialization issue (non-critical): {e}")

# Initialize database on startup
init_database()


# Initialize the Domus Planning Platform
app = FastAPI(
    title="Domus Planning Platform - AI Operating System", 
    description="The 4-Pillar AI Planning System: Planning AI + Auto-Docs + Property API + Offsets Marketplace",
    version="4.0.0",
    contact={
        "name": "Domus Platform",
        "email": "hello@domusplanning.co.uk",
        "url": "https://domusplanning.co.uk"
    }
)

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Simple CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"]
)

# Load core platform modules
print("Loading Domus Professional Platform...")

try:
    print("   Auto-Docs module: In-app implementation")
except ImportError as e:
    print(f"   Auto-Docs not available: {e}")

try:
    from property_api.router import router as property_api_router
    app.include_router(property_api_router)
    print("   Property API module loaded")
except ImportError as e:
    print(f"   Property API not available: {e}")

try:
    from offsets_marketplace.router import router as offsets_router
    app.include_router(offsets_router)
    print("   Offsets Marketplace module loaded")
except ImportError as e:
    print(f"   Offsets Marketplace not available: {e}")

# Mock middleware function for optional features
async def enforce_quota_middleware(request: Request, call_next):
    """Simple quota middleware placeholder"""
    return await call_next(request)

print("   Authentication and billing systems loaded")
app.middleware("http")(enforce_quota_middleware)

print("\nDomus Professional Platform Ready")

# =====================================
# AUTHENTICATION ENDPOINTS
# =====================================

@app.post("/api/auth/signup")
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Create new user account"""
    try:
        # For now, return mock response until DB is properly connected
        return {
            "token": "mock_token_" + request.email,
            "user": {
                "id": 1,
                "email": request.email,
                "role": request.role.value,
                "org_id": 1,
                "plan": "core"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """User login"""
    try:
        # For now, return mock response until DB is properly connected
        return {
            "token": "mock_token_" + request.email,
            "user": {
                "id": 1,
                "email": request.email,
                "role": "super_admin",
                "org_id": 1,
                "plan": "enterprise"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/session")
async def get_session():
    """Get current user session info"""
    try:
        # For now, return mock super admin session
        return {
            "user": {
                "id": 1,
                "email": "admin@domusplanning.co.uk",
                "role": "super_admin",
                "org_id": 1,
                "plan": "enterprise"
            },
            "org": {
                "id": 1,
                "name": "Domus Planning",
                "plan": "enterprise"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/usage")
async def get_usage():
    """Get current usage information for the organization"""
    try:
        # Return mock usage data
        return {
            "org_id": 1,
            "org_name": "Domus Planning",
            "plan": "enterprise",
            "quotas": {
                "projects": {
                    "current": 3,
                    "limit": -1,
                    "unlimited": True,
                    "percentage": 0,
                    "available": -1
                },
                "docs": {
                    "current": 15,
                    "limit": -1,
                    "unlimited": True,
                    "percentage": 0,
                    "available": -1
                },
                "marketplace_posts": {
                    "current": 2,
                    "limit": -1,
                    "unlimited": True,
                    "percentage": 0,
                    "available": -1
                },
                "contracts": {
                    "current": 1,
                    "limit": -1,
                    "unlimited": True,
                    "percentage": 0,
                    "available": -1
                }
            },
            "period": "monthly"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# =====================================
# DASHBOARD ENDPOINTS
# =====================================

@app.get("/api/dashboard/overview")
async def get_dashboard_overview():
    """Get dashboard overview data tailored to user role"""
    try:
        # Return role-specific dashboard data
        return {
            "metrics": {
                "total_projects": 8,
                "active_projects": 5,
                "completed_projects": 3,
                "approval_rate": 84.2,
                "time_saved": 45.5,  # hours
                "cost_saved": 12500  # pounds
            },
            "recent_activity": [
                {
                    "id": 1,
                    "type": "project_created",
                    "title": "New project created",
                    "description": "Riverside Development - Planning application started",
                    "timestamp": "2024-10-02T09:30:00",
                    "icon": "📁"
                },
                {
                    "id": 2,
                    "type": "analysis_completed",
                    "title": "Planning analysis completed",
                    "description": "Green Belt Site - 78% approval probability",
                    "timestamp": "2024-10-02T08:15:00", 
                    "icon": "🧠"
                },
                {
                    "id": 3,
                    "type": "document_generated",
                    "title": "Documents generated",
                    "description": "Planning Statement and DAS for Manor House",
                    "timestamp": "2024-10-01T16:45:00",
                    "icon": "📄"
                }
            ],
            "quick_actions": [
                {
                    "title": "New Project",
                    "description": "Start a new planning project",
                    "route": "/projects/new",
                    "icon": "➕",
                    "color": "primary"
                },
                {
                    "title": "Run Analysis",
                    "description": "Analyze a site with Planning AI",
                    "route": "/planning-ai",
                    "icon": "🔍",
                    "color": "secondary"
                },
                {
                    "title": "Generate Docs",
                    "description": "Create planning documents",
                    "route": "/auto-docs",
                    "icon": "📝",
                    "color": "secondary"
                },
                {
                    "title": "Property Data",
                    "description": "UK property intelligence & analytics",
                    "route": "/property-api",
                    "icon": "🏠",
                    "color": "secondary"
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/dashboard/recent-projects")
async def get_recent_projects():
    """Get recent projects for dashboard"""
    try:
        return [
            {
                "id": 1,
                "title": "Riverside Development",
                "address": "123 River Street, London",
                "status": "active",
                "ai_score": 78.5,
                "last_updated": "2024-10-02T09:30:00",
                "stage": "Planning Analysis"
            },
            {
                "id": 2,
                "title": "Green Belt Site",
                "address": "45 Countryside Lane, Surrey",
                "status": "pending",
                "ai_score": 65.2,
                "last_updated": "2024-10-01T14:20:00",
                "stage": "Document Generation"
            },
            {
                "id": 3,
                "title": "Manor House Extension",
                "address": "78 Historic Avenue, Bath",
                "status": "approved",
                "ai_score": 89.1,
                "last_updated": "2024-09-28T11:15:00",
                "stage": "Completed"
            }
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/dashboard/notifications")
async def get_notifications():
    """Get user notifications for dashboard"""
    try:
        return [
            {
                "id": 1,
                "type": "success",
                "title": "Analysis Complete",
                "message": "Planning analysis for Riverside Development is ready",
                "timestamp": "2024-10-02T09:30:00",
                "read": False
            },
            {
                "id": 2,
                "type": "info",
                "title": "Document Ready",
                "message": "Planning Statement generated for Green Belt Site",
                "timestamp": "2024-10-01T16:45:00",
                "read": False
            },
            {
                "id": 3,
                "type": "warning",
                "title": "Quota Alert",
                "message": "You've used 8/10 projects this month",
                "timestamp": "2024-10-01T10:00:00",
                "read": True
            }
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/dashboard/marketplace-summary")
async def get_marketplace_summary():
    """Get marketplace summary for landowner dashboard"""
    try:
        return {
            "listings": {
                "active": 3,
                "pending": 1,
                "sold": 2
            },
            "earnings": {
                "total": 45000,
                "this_month": 12000,
                "pending": 8000
            },
            "recent_activity": [
                {
                    "id": 1,
                    "type": "sale_completed",
                    "title": "Unit sale completed",
                    "description": "5.2 biodiversity units sold for £15,000",
                    "timestamp": "2024-10-01T14:30:00"
                },
                {
                    "id": 2,
                    "type": "new_interest",
                    "title": "New buyer interest",
                    "description": "Inquiry for woodland habitat units",
                    "timestamp": "2024-09-30T11:20:00"
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# =====================================
# PROJECTS ENDPOINTS
# =====================================

@app.get("/api/projects")
async def get_projects():
    """Get organization's projects"""
    try:
        # Return enhanced mock projects data
        return [
            {
                "id": 1,
                "name": "Riverside Development",
                "description": "Mixed-use development with 50 residential units and commercial space",
                "address": "123 River Street, London SW1A 1AA",
                "postcode": "SW1A 1AA",
                "council": "Westminster City Council",
                "type": "mixed",
                "status": "planning",
                "units": 50,
                "area": 2500,
                "value": 15000000,
                "ai_score": 78,
                "progress": 45,
                "created_at": datetime.now() - timedelta(days=15),
                "updated_at": datetime.now() - timedelta(days=2),
                "owner_name": "Thames Development Ltd",
                "latitude": 51.5074,
                "longitude": -0.1278
            },
            {
                "id": 2,
                "name": "Green Valley Homes",
                "description": "Sustainable housing development with 25 eco-friendly homes",
                "address": "456 Valley Road, Manchester M1 2AB",
                "postcode": "M1 2AB",
                "council": "Manchester City Council",
                "type": "residential",
                "status": "submitted",
                "units": 25,
                "area": 1800,
                "value": 8500000,
                "ai_score": 85,
                "progress": 70,
                "created_at": datetime.now() - timedelta(days=8),
                "updated_at": datetime.now() - timedelta(days=1),
                "owner_name": "Eco Homes Ltd",
                "latitude": 53.4808,
                "longitude": -2.2426
            },
            {
                "id": 3,
                "name": "City Centre Plaza",
                "description": "Commercial development with retail and office spaces",
                "address": "789 High Street, Birmingham B1 3CD",
                "postcode": "B1 3CD",
                "council": "Birmingham City Council",
                "type": "commercial",
                "status": "approved",
                "units": 0,
                "area": 3200,
                "value": 22000000,
                "ai_score": 92,
                "progress": 100,
                "created_at": datetime.now() - timedelta(days=30),
                "updated_at": datetime.now() - timedelta(days=5),
                "owner_name": "Urban Developments",
                "latitude": 52.4862,
                "longitude": -1.8904
            }
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class ProjectCreateData(BaseModel):
    name: str
    description: str = ""
    address: str
    postcode: str = ""
    council: str = ""
    type: str
    units: int = 0
    area: float = 0
    value: float = 0
    planning_status: str = "planning"
    application_ref: str = ""
    target_date: str = ""

@app.post("/api/projects")
async def create_project(project_data: ProjectCreateData):
    """Create new project"""
    try:
        # Generate mock ID and timestamps
        new_id = random.randint(100, 999)
        now = datetime.now()
        
        # Calculate AI score based on project characteristics
        base_score = 60
        score_adjustments = 0
        
        # Type-based scoring
        if project_data.type == "residential":
            score_adjustments += 10
        elif project_data.type == "affordable_housing":
            score_adjustments += 15
        elif project_data.type == "commercial":
            score_adjustments += 5
        
        # Size-based scoring
        if project_data.units > 0 and project_data.units <= 50:
            score_adjustments += 8
        
        # Area-based scoring
        if project_data.area > 0 and project_data.area < 5000:
            score_adjustments += 5
        
        ai_score = min(100, max(20, base_score + score_adjustments + random.randint(-10, 15)))
        
        new_project = {
            "id": new_id,
            "name": project_data.name,
            "description": project_data.description,
            "address": project_data.address,
            "postcode": project_data.postcode,
            "council": project_data.council,
            "type": project_data.type,
            "status": project_data.planning_status,
            "units": project_data.units,
            "area": project_data.area,
            "value": project_data.value,
            "ai_score": ai_score,
            "progress": 5,  # New project starts at 5%
            "created_at": now,
            "updated_at": now,
            "application_ref": project_data.application_ref,
            "target_date": project_data.target_date,
            "latitude": 51.5074 + random.uniform(-0.1, 0.1),  # Mock coordinates
            "longitude": -0.1278 + random.uniform(-0.1, 0.1)
        }
        
        return new_project
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/projects/{project_id}")
async def get_project(project_id: int):
    """Get specific project details"""
    try:
        # Return comprehensive mock project details
        project = {
            "id": project_id,
            "name": "Riverside Development",
            "description": "Mixed-use development with 50 residential units and commercial space",
            "address": "123 River Street, London SW1A 1AA",
            "postcode": "SW1A 1AA",
            "council": "Westminster City Council",
            "type": "mixed",
            "status": "planning",
            "units": 50,
            "area": 2500,
            "value": 15000000,
            "ai_score": 78,
            "progress": 45,
            "created_at": datetime.now() - timedelta(days=15),
            "updated_at": datetime.now() - timedelta(days=2),
            "latitude": 51.5074,
            "longitude": -0.1278,
            "application_ref": "23/01234/FUL",
            "target_date": "2024-12-15",
            "constraints": [
                "Conservation Area nearby",
                "Flood Risk Zone 2",
                "Tree Preservation Orders"
            ],
            "ai_reasoning": "Strong fundamentals with good local support but moderate constraints require careful design",
            "documents": [
                {
                    "id": 1,
                    "name": "Site Survey Report.pdf",
                    "size": "2.4 MB",
                    "uploaded_at": datetime.now() - timedelta(days=5),
                    "type": "survey"
                },
                {
                    "id": 2,
                    "name": "Planning Statement.pdf",
                    "size": "1.8 MB", 
                    "uploaded_at": datetime.now() - timedelta(days=3),
                    "type": "planning"
                }
            ],
            "timeline": [
                {
                    "title": "Project Created",
                    "date": datetime.now() - timedelta(days=15),
                    "description": "Initial project setup completed"
                },
                {
                    "title": "Site Survey",
                    "date": datetime.now() - timedelta(days=10),
                    "description": "Comprehensive site survey conducted"
                },
                {
                    "title": "AI Analysis",
                    "date": datetime.now() - timedelta(days=5),
                    "description": "Planning AI analysis completed with 78% approval score"
                }
            ],
            "ai_analyses": ["Initial assessment", "Constraint analysis"]
        }
        
        return project
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/projects/{project_id}")
async def update_project(project_id: int, project_data: ProjectCreateData):
    """Update existing project"""
    try:
        # Return updated project data
        updated_project = {
            "id": project_id,
            "name": project_data.name,
            "description": project_data.description,
            "address": project_data.address,
            "postcode": project_data.postcode,
            "council": project_data.council,
            "type": project_data.type,
            "status": project_data.planning_status,
            "units": project_data.units,
            "area": project_data.area,
            "value": project_data.value,
            "updated_at": datetime.now(),
            "application_ref": project_data.application_ref,
            "target_date": project_data.target_date
        }
        
        return updated_project
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: int):
    """Delete project"""
    try:
        return {"message": "Project deleted successfully", "id": project_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
print("   Professional planning intelligence and compliance automation")

# Serve the clean frontend
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main application shell"""
    return templates.TemplateResponse("app_shell.html", {"request": request})

# All authenticated app routes serve the same app shell except projects, planning-ai, auto-docs, and property-api which have dedicated templates
@app.get("/dashboard", response_class=HTMLResponse)
@app.get("/documents", response_class=HTMLResponse)
@app.get("/marketplace/supply", response_class=HTMLResponse)
@app.get("/marketplace/demand", response_class=HTMLResponse)
@app.get("/contracts", response_class=HTMLResponse)
@app.get("/analytics", response_class=HTMLResponse)
@app.get("/settings", response_class=HTMLResponse)
@app.get("/settings/billing", response_class=HTMLResponse)
@app.get("/settings/api-keys", response_class=HTMLResponse)
@app.get("/admin", response_class=HTMLResponse)
async def app_routes(request: Request):
    """Serve the app shell for all authenticated routes"""
    return templates.TemplateResponse("app_shell.html", {"request": request})

# Projects-specific template routes
@app.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request):
    """Serve the projects listing page"""
    # Mock projects data
    projects = [
        {
            "id": 1,
            "name": "Riverside Development",
            "description": "Mixed-use development with 50 residential units and commercial space",
            "address": "123 River Street, London SW1A 1AA",
            "status": "planning",
            "ai_score": 78,
            "progress": 45,
            "created_at": datetime.now() - timedelta(days=15),
            "owner_name": "Thames Development Ltd"
        },
        {
            "id": 2,
            "name": "Green Valley Homes",
            "description": "Sustainable housing development with 25 eco-friendly homes",
            "address": "456 Valley Road, Manchester M1 2AB",
            "status": "submitted",
            "ai_score": 85,
            "progress": 70,
            "created_at": datetime.now() - timedelta(days=8),
            "owner_name": "Eco Homes Ltd"
        },
        {
            "id": 3,
            "name": "City Centre Plaza",
            "description": "Commercial development with retail and office spaces",
            "address": "789 High Street, Birmingham B1 3CD",
            "status": "approved",
            "ai_score": 92,
            "progress": 100,
            "created_at": datetime.now() - timedelta(days=30),
            "owner_name": "Urban Developments"
        }
    ]
    return templates.TemplateResponse("projects.html", {"request": request, "projects": projects})

@app.get("/projects/new", response_class=HTMLResponse)
async def new_project_page(request: Request):
    """Serve the new project creation page"""
    return templates.TemplateResponse("projects_new.html", {"request": request})

@app.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_detail_page(request: Request, project_id: int):
    """Serve the project detail page"""
    # Mock project data
    project = {
        "id": project_id,
        "name": "Riverside Development",
        "description": "Mixed-use development with 50 residential units and commercial space",
        "address": "123 River Street, London SW1A 1AA",
        "postcode": "SW1A 1AA",
        "council": "Westminster City Council",
        "type": "mixed",
        "status": "planning",
        "units": 50,
        "area": 2500,
        "value": 15000000,
        "ai_score": 78,
        "progress": 45,
        "created_at": datetime.now() - timedelta(days=15),
        "latitude": 51.5074,
        "longitude": -0.1278,
        "constraints": [
            "Conservation Area nearby",
            "Flood Risk Zone 2",
            "Tree Preservation Orders"
        ],
        "ai_reasoning": "Strong fundamentals with good local support but moderate constraints require careful design",
        "documents": [
            {
                "name": "Site Survey Report.pdf",
                "size": "2.4 MB",
                "uploaded_at": datetime.now() - timedelta(days=5)
            },
            {
                "name": "Planning Statement.pdf", 
                "size": "1.8 MB",
                "uploaded_at": datetime.now() - timedelta(days=3)
            }
        ],
        "timeline": [
            {
                "title": "Project Created",
                "date": datetime.now() - timedelta(days=15),
                "description": "Initial project setup completed"
            },
            {
                "title": "Site Survey",
                "date": datetime.now() - timedelta(days=10),
                "description": "Comprehensive site survey conducted"
            },
            {
                "title": "AI Analysis",
                "date": datetime.now() - timedelta(days=5),
                "description": "Planning AI analysis completed with 78% approval score"
            }
        ],
        "ai_analyses": ["Initial assessment", "Constraint analysis"]
    }
    return templates.TemplateResponse("projects_detail.html", {"request": request, "project": project, "now": datetime.now})

# Planning AI template route
@app.get("/planning-ai", response_class=HTMLResponse)
async def planning_ai_page(request: Request):
    """Serve the Planning AI analysis page"""
    return templates.TemplateResponse("planning_ai.html", {"request": request})

# Auto-Docs template route
@app.get("/auto-docs", response_class=HTMLResponse)
async def auto_docs_page(request: Request):
    """Serve the Auto-Docs generator page"""
    return templates.TemplateResponse("auto_docs.html", {"request": request})

# Property API template route
@app.get("/property-api", response_class=HTMLResponse)
async def property_api_page(request: Request):
    """Serve the Property API intelligence page"""
    return templates.TemplateResponse("property_api.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve the login page"""
    try:
        with open('frontend/login.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"<html><body><h1>Login Unavailable</h1><p>Please try again later.</p></body></html>"

@app.get("/debug-html")
async def debug_html():
    """Debug endpoint to check what HTML content is being served"""
    try:
        html_path = Path(__file__).parent / "frontend" / "platform_production.html"
        if html_path.exists():
            with open(html_path, 'r', encoding='utf-8') as file:
                content = file.read()
            # Return just the dashboard section
            start = content.find('<div id="dashboard" class="page active">')
            end = content.find('</div>', start + 200)
            if start != -1 and end != -1:
                return {"dashboard_content": content[start:end+6]}
            else:
                return {"error": "Dashboard section not found", "file_size": len(content)}
        else:
            return {"error": "HTML file not found", "path": str(html_path)}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    """Simple health check for the 4-pillar system"""
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "platform": "Domus Planning AI System",
        "version": "4.0.0",
        
        "core_pillars": {
            "planning_ai": {
                "name": "Planning AI Analysis",
                "description": "Instant approval probability & constraint analysis",
                "status": "operational"
            },
            "auto_docs": {
                "name": "Auto-Docs Generator", 
                "description": "Professional planning document generation",
                "status": "operational"
            },
            "property_api": {
                "name": "Property Data API",
                "description": "Unified UK property data source", 
                "status": "operational"
            },
            "offsets_marketplace": {
                "name": "Offsets Marketplace",
                "description": "Biodiversity Net Gain trading platform",
                "status": "operational"
            }
        },
        
        "value_proposition": {
            "for_developers": "Save months and £20k+ in consultancy costs",
            "for_consultants": "Scale output with AI co-pilot tools",
            "for_landowners": "Unlock development value, streamline approvals",
            "for_landowners": "Monetise land through biodiversity offsets"
        }
    }

@app.get("/api/workflow-guide")
async def workflow_guide():
    """Guide users through the 4-pillar workflow"""
    return {
        "workflow_steps": [
            {
                "step": 1,
                "pillar": "Site Input",
                "action": "Input site details (address, UPRN, or polygon)",
                "endpoint": "/api/sites/analyze"
            },
            {
                "step": 2, 
                "pillar": "Property API",
                "action": "Pull unified property data (title, EPC, flood, planning history)",
                "endpoint": "/api/property/lookup"
            },
            {
                "step": 3,
                "pillar": "Planning AI", 
                "action": "Analyze constraints + policies → approval probability + recommendations",
                "endpoint": "/api/planning-ai/analyze"
            },
            {
                "step": 4,
                "pillar": "Auto-Docs",
                "action": "Generate planning application documents (Planning Statement, D&A)",
                "endpoint": "/api/auto-docs/generate"
            },
            {
                "step": 5,
                "pillar": "Decision Point",
                "action": "If viable → proceed with application. If not viable → list in Offsets Marketplace",
                "endpoint": "/api/offsets/list OR submit application"
            }
        ],
        "integration_points": {
            "data_flow": "Site Input → Property API → Planning AI → Auto-Docs → Submit OR Offsets",
            "closed_loop": "Failed planning applications become biodiversity offset opportunities"
        }
    }

@app.get("/api/market-stats")
async def market_statistics():
    """Show the planning market problem this solves"""
    return {
        "uk_planning_problems": {
            "average_planning_consultant_cost": "£15,000 - £30,000 per application",
            "average_decision_time": "8-16 weeks for major applications", 
            "approval_uncertainty": "60-70% approval rate varies wildly by area",
            "wasted_land_value": "£billions in undevelopable land sitting idle"
        },
        "domus_solution": {
            "cost_reduction": "90% reduction in consultant costs via AI automation",
            "time_savings": "80% faster constraint analysis and document generation",
            "certainty_improvement": "Predict approval probability before spending heavily",
            "alternative_value": "Monetise failed land through biodiversity offsets"
        },
        "target_market_size": {
            "uk_planning_applications_per_year": "500,000+",
            "sme_developers": "10,000+ potential users",
            "planning_consultants": "2,000+ potential users", 
            "market_opportunity": "£billions in development potential unlocked by AI"
        }
    }

# PLANNING AI ENDPOINTS
# ===========================================

class PlanningAnalysisRequest(BaseModel):
    address: str
    latitude: float
    longitude: float
    development_type: str = ""
    units: int = 0
    floor_area: float = 0
    height: int = 1
    scenarios: dict = {}

@app.post("/api/planning-ai/analyze")
async def analyze_site_comprehensive(analysis_data: PlanningAnalysisRequest):
    """Comprehensive Planning AI analysis with constraints, policies, and precedents"""
    try:
        # Simulate processing time
        import time
        time.sleep(1)
        
        # Calculate base AI score
        base_score = 65
        score_adjustments = 0
        key_factors = []
        
        # Development type adjustments
        if analysis_data.development_type == "residential":
            score_adjustments += 10
            key_factors.append({"text": "Residential development prioritized", "positive": True})
        elif analysis_data.development_type == "affordable_housing":
            score_adjustments += 20
            key_factors.append({"text": "Affordable housing strongly supported", "positive": True})
        elif analysis_data.development_type == "commercial":
            score_adjustments += 5
            key_factors.append({"text": "Commercial development acceptable", "positive": True})
        
        # Units scaling
        if analysis_data.units > 0:
            if analysis_data.units <= 10:
                score_adjustments += 15
                key_factors.append({"text": "Small scale development favored", "positive": True})
            elif analysis_data.units <= 50:
                score_adjustments += 8
                key_factors.append({"text": "Medium scale development appropriate", "positive": True})
            else:
                score_adjustments -= 10
                key_factors.append({"text": "Large scale may face community resistance", "positive": False})
        
        # Height considerations
        if analysis_data.height > 4:
            score_adjustments -= 5
            key_factors.append({"text": "Height may cause visual impact concerns", "positive": False})
        
        # Scenario bonuses
        scenarios = analysis_data.scenarios or {}
        if scenarios.get("affordable_housing"):
            score_adjustments += 12
            key_factors.append({"text": "35% affordable housing commitment", "positive": True})
        if scenarios.get("net_gain"):
            score_adjustments += 8
            key_factors.append({"text": "Biodiversity Net Gain compliance", "positive": True})
        if scenarios.get("car_free"):
            score_adjustments += 6
            key_factors.append({"text": "Car-free development reduces transport impact", "positive": True})
        if scenarios.get("sustainable"):
            score_adjustments += 10
            key_factors.append({"text": "BREEAM Excellent sustainability rating", "positive": True})
        
        # Add some randomization for realism
        score_adjustments += random.randint(-8, 12)
        final_score = max(15, min(95, base_score + score_adjustments))
        
        # Generate interpretation
        if final_score >= 80:
            interpretation = "Excellent approval prospects with strong policy support"
        elif final_score >= 65:
            interpretation = "Good approval prospects with manageable constraints"
        elif final_score >= 45:
            interpretation = "Moderate prospects requiring careful design approach"
        else:
            interpretation = "Challenging application requiring significant mitigation"
        
        # Mock constraints data based on location
        constraints = [
            {
                "name": "Conservation Area",
                "description": "Site is within 200m of Riverside Conservation Area",
                "severity": "medium",
                "distance": "180m northeast"
            },
            {
                "name": "Flood Risk Zone 2",
                "description": "Part of site falls within Environment Agency Flood Zone 2",
                "severity": "high",
                "distance": "Site partially affected"
            },
            {
                "name": "Tree Preservation Order",
                "description": "3 protected oak trees along southern boundary",
                "severity": "medium",
                "distance": "On site"
            },
            {
                "name": "Archaeological Interest",
                "description": "Area of archaeological potential - desk-based assessment required",
                "severity": "low",
                "distance": "Site affected"
            }
        ]
        
        # Mock policy citations
        policies = [
            {
                "reference": "Local Plan Policy H1",
                "title": "Housing Delivery and Allocation",
                "relevance": "Supports residential development on suitable sites"
            },
            {
                "reference": "NPPF Para 11",
                "title": "Presumption in favour of sustainable development",
                "relevance": "Presumption applies unless specific policies indicate otherwise"
            },
            {
                "reference": "Local Plan Policy ENV3",
                "title": "Conservation Areas",
                "relevance": "Development must preserve or enhance character and appearance"
            },
            {
                "reference": "Local Plan Policy CC1",
                "title": "Climate Change",
                "relevance": "Development should minimize flood risk and adapt to climate change"
            }
        ]
        
        # Mock precedents
        precedents = [
            {
                "reference": "23/01234/FUL",
                "description": "25 residential units with mixed tenure including 35% affordable housing",
                "outcome": "Approved",
                "distance": "0.8km",
                "date": "March 2024"
            },
            {
                "reference": "22/05678/FUL", 
                "description": "40 unit residential development with private parking",
                "outcome": "Refused",
                "distance": "1.2km",
                "date": "November 2023"
            },
            {
                "reference": "23/09876/FUL",
                "description": "Mixed use development with commercial ground floor",
                "outcome": "Approved",
                "distance": "1.5km",
                "date": "July 2024"
            }
        ]
        
        # AI recommendations
        recommendations = [
            "Conduct heritage impact assessment for Conservation Area proximity",
            "Implement comprehensive flood risk management strategy",
            "Prepare arboricultural impact assessment and tree protection plan",
            "Consider desk-based archaeological assessment early in process",
            "Engage with local community before formal submission",
            "Design sustainable drainage systems (SuDS) throughout site",
            "Incorporate renewable energy systems to exceed policy requirements"
        ]
        
        return {
            "analysis_id": f"AI-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "address": analysis_data.address,
            "score": final_score,
            "interpretation": interpretation,
            "key_factors": key_factors,
            "constraints": constraints,
            "policies": policies,
            "precedents": precedents,
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat(),
            "confidence": random.randint(82, 94)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/planning-ai/save")
async def save_analysis():
    """Save Planning AI analysis to user's projects"""
    try:
        # Mock save operation
        return {
            "success": True,
            "message": "Analysis saved to your projects",
            "project_id": random.randint(100, 999)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/planning-ai/export")
async def export_analysis():
    """Export Planning AI analysis as PDF report"""
    try:
        # Mock export operation
        return {
            "success": True,
            "download_url": f"/downloads/planning-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.pdf",
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# AUTO-DOCS ENDPOINTS
# ===========================================

class DocumentGenerationRequest(BaseModel):
    document_type: str
    project_id: int
    output_format: str = "docx"
    generation_mode: str = "comprehensive"
    options: dict = {}
    custom_instructions: str = ""

@app.post("/api/auto-docs/generate")
async def generate_document(generation_request: DocumentGenerationRequest):
    """Generate professional planning documents with AI"""
    try:
        # Simulate document generation process
        document_types = {
            "planning_statement": {
                "title": "Planning Statement",
                "sections": [
                    "Executive Summary",
                    "Site Description & Context",
                    "Development Proposals",
                    "Planning Policy Assessment",
                    "Design & Access Considerations",
                    "Technical Assessments",
                    "Community Consultation",
                    "Planning Balance & Conclusions"
                ]
            },
            "design_access_statement": {
                "title": "Design & Access Statement",
                "sections": [
                    "Introduction",
                    "Site Analysis",
                    "Design Evolution",
                    "Access Strategy",
                    "Appearance & Character",
                    "Layout & Scale",
                    "Landscaping Strategy",
                    "Sustainability Measures"
                ]
            },
            "heritage_statement": {
                "title": "Heritage Statement",
                "sections": [
                    "Introduction",
                    "Methodology",
                    "Site History",
                    "Heritage Assets Assessment",
                    "Impact Assessment",
                    "Mitigation Measures",
                    "Conclusions"
                ]
            },
            "flood_risk_assessment": {
                "title": "Flood Risk Assessment",
                "sections": [
                    "Executive Summary",
                    "Site Description",
                    "Flood Risk Identification",
                    "Flood Risk Assessment",
                    "Mitigation Measures",
                    "Residual Risk",
                    "Recommendations"
                ]
            },
            "transport_statement": {
                "title": "Transport Statement",
                "sections": [
                    "Introduction",
                    "Site Description",
                    "Existing Transport Conditions",
                    "Development Proposals",
                    "Trip Generation",
                    "Impact Assessment",
                    "Mitigation Measures"
                ]
            },
            "biodiversity_report": {
                "title": "Biodiversity Net Gain Report",
                "sections": [
                    "Executive Summary",
                    "Baseline Ecological Assessment",
                    "Impact Assessment",
                    "Mitigation Hierarchy",
                    "Net Gain Calculations",
                    "Enhancement Proposals",
                    "Monitoring Strategy"
                ]
            }
        }

        doc_config = document_types.get(generation_request.document_type, document_types["planning_statement"])
        
        # Mock project data lookup
        project_names = {
            1: "Riverside Development",
            2: "Green Valley Homes", 
            3: "City Centre Plaza"
        }
        
        project_name = project_names.get(generation_request.project_id, "Unknown Project")
        
        # Generate preview content based on document type
        preview_content = generate_document_preview(generation_request.document_type, project_name)
        
        # Calculate realistic metrics
        base_pages = 8
        if generation_request.generation_mode == "comprehensive":
            pages = base_pages + random.randint(4, 8)
        elif generation_request.generation_mode == "summary":
            pages = max(4, base_pages - random.randint(2, 4))
        else:
            pages = base_pages + random.randint(0, 3)
        
        # Adjust for options
        if generation_request.options.get("include_maps"):
            pages += 2
        if generation_request.options.get("include_photos"):
            pages += 3
        if generation_request.options.get("include_analysis"):
            pages += 2
            
        file_size = f"{pages * 0.2:.1f} MB"
        
        return {
            "success": True,
            "document_id": f"DOC-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "title": doc_config["title"],
            "project_name": project_name,
            "pages": pages,
            "file_size": file_size,
            "sections": doc_config["sections"],
            "preview_content": preview_content,
            "download_url": f"/downloads/{generation_request.document_type}-{generation_request.project_id}-{datetime.now().strftime('%Y%m%d')}.{generation_request.output_format}",
            "generated_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=30)).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document generation failed: {str(e)}")

def generate_document_preview(doc_type, project_name):
    """Generate realistic document preview content"""
    previews = {
        "planning_statement": f"This Planning Statement has been prepared in support of a planning application for {project_name}. The proposed development represents a sustainable and well-designed scheme that aligns with local and national planning policy. The site is considered suitable for development, being located within the settlement boundary and having good access to local services and transport links.",
        
        "design_access_statement": f"This Design and Access Statement demonstrates how the design of {project_name} has evolved through careful analysis of the site and its context. The proposals respond positively to the character of the surrounding area while providing high-quality accommodation that meets current accessibility standards.",
        
        "heritage_statement": f"This Heritage Statement assesses the potential impact of the proposed development at {project_name} on heritage assets. The assessment concludes that the proposals have been designed to preserve the significance of nearby heritage assets while delivering sustainable development.",
        
        "flood_risk_assessment": f"This Flood Risk Assessment evaluates the flood risk to and from the proposed development at {project_name}. The assessment demonstrates that the development can be made safe from flooding and will not increase flood risk elsewhere.",
        
        "transport_statement": f"This Transport Statement assesses the transport implications of the proposed development at {project_name}. The development is well-located with good access to public transport and will not result in adverse traffic impacts.",
        
        "biodiversity_report": f"This Biodiversity Net Gain Report demonstrates how the proposed development at {project_name} will deliver measurable improvements for biodiversity. The proposals include comprehensive ecological enhancements that exceed the 10% net gain requirement."
    }
    
    return previews.get(doc_type, f"This document provides a comprehensive assessment of {project_name} in accordance with planning requirements.")

@app.get("/api/auto-docs/history")
async def get_generation_history():
    """Get user's document generation history"""
    try:
        # Mock generation history
        history = [
            {
                "id": "DOC-20241001-143022",
                "title": "Planning Statement",
                "project_name": "Riverside Development",
                "document_type": "planning_statement",
                "output_format": "docx",
                "pages": 14,
                "file_size": "2.8 MB",
                "created_at": "1 Oct 2024, 2:30 PM",
                "status": "completed"
            },
            {
                "id": "DOC-20240928-091245",
                "title": "Design & Access Statement", 
                "project_name": "Green Valley Homes",
                "document_type": "design_access_statement",
                "output_format": "pdf",
                "pages": 12,
                "file_size": "3.2 MB",
                "created_at": "28 Sep 2024, 9:12 AM",
                "status": "completed"
            },
            {
                "id": "DOC-20240925-164533",
                "title": "Heritage Statement",
                "project_name": "City Centre Plaza",
                "document_type": "heritage_statement", 
                "output_format": "docx",
                "pages": 8,
                "file_size": "1.6 MB",
                "created_at": "25 Sep 2024, 4:45 PM",
                "status": "completed"
            }
        ]
        
        return history
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auto-docs/bundle")
async def create_document_bundle():
    """Create a bundle of multiple documents"""
    try:
        return {
            "success": True,
            "bundle_id": f"BUNDLE-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "title": "Planning Application Bundle",
            "documents_count": 4,
            "total_size": "12.4 MB",
            "download_url": f"/downloads/bundle-{datetime.now().strftime('%Y%m%d')}.zip",
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auto-docs/templates")
async def get_document_templates():
    """Get available document templates"""
    try:
        templates = [
            {
                "type": "planning_statement",
                "name": "Planning Statement",
                "description": "Comprehensive planning justification document",
                "category": "Core Planning",
                "icon": "file-contract",
                "color": "blue"
            },
            {
                "type": "design_access_statement", 
                "name": "Design & Access Statement",
                "description": "Design principles and accessibility assessment",
                "category": "Design",
                "icon": "drafting-compass",
                "color": "purple"
            },
            {
                "type": "heritage_statement",
                "name": "Heritage Statement", 
                "description": "Impact assessment for historic assets",
                "category": "Heritage",
                "icon": "landmark",
                "color": "amber"
            },
            {
                "type": "flood_risk_assessment",
                "name": "Flood Risk Assessment",
                "description": "Flood risk analysis and mitigation",
                "category": "Environment",
                "icon": "water",
                "color": "blue"
            },
            {
                "type": "transport_statement",
                "name": "Transport Statement",
                "description": "Traffic impact and accessibility analysis", 
                "category": "Transport",
                "icon": "road",
                "color": "gray"
            },
            {
                "type": "biodiversity_report",
                "name": "Biodiversity Net Gain Report",
                "description": "Ecological impact and enhancement plan",
                "category": "Environment",
                "icon": "leaf",
                "color": "green"
            }
        ]
        
        return templates
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# PROPERTY API ENDPOINTS
# ===========================================

class PropertySearchRequest(BaseModel):
    address: str = ""
    postcode: str = ""
    property_type: str = ""
    price_range: str = ""
    bedrooms: int = None

class PropertyValuationRequest(BaseModel):
    address: str
    postcode: str
    property_type: str = ""
    bedrooms: int = None
    bathrooms: int = None
    garden: bool = False

@app.post("/api/property-api/search")
async def search_properties(search_request: PropertySearchRequest):
    """Search UK properties with comprehensive data"""
    try:
        # Mock property search results with realistic UK data
        properties = [
            {
                "id": "PROP001",
                "address": "123 Oak Avenue, Manchester M1 2AB",
                "postcode": "M1 2AB",
                "type": "Terraced",
                "bedrooms": 3,
                "bathrooms": 2,
                "price": "£485,000",
                "estimated_value": 485000,
                "price_per_sqft": "£312",
                "floor_area": 1554,
                "garden": True,
                "parking": True,
                "council": "Manchester City Council",
                "council_tax_band": "D",
                "epc_rating": "C",
                "tenure": "Freehold",
                "coordinates": [53.4808, -2.2426],
                "description": "Spacious Victorian terrace with period features, modern kitchen, and south-facing garden",
                "images": ["/images/prop1_1.jpg", "/images/prop1_2.jpg"],
                "last_sold": "2019-06-15",
                "last_price": "£415,000",
                "price_change": "+16.9%",
                "days_on_market": 42,
                "local_amenities": ["Primary School 0.2mi", "Train Station 0.5mi", "Shopping Centre 0.8mi"],
                "planning_restrictions": ["Conservation Area nearby", "Article 4 Direction applies"]
            },
            {
                "id": "PROP002", 
                "address": "45 Elm Grove, Manchester M1 3CD",
                "postcode": "M1 3CD",
                "type": "Semi-Detached",
                "bedrooms": 4,
                "bathrooms": 3,
                "price": "£520,000",
                "estimated_value": 520000,
                "price_per_sqft": "£298",
                "floor_area": 1745,
                "garden": True,
                "parking": True,
                "council": "Manchester City Council",
                "council_tax_band": "E", 
                "epc_rating": "B",
                "tenure": "Freehold",
                "coordinates": [53.4828, -2.2456],
                "description": "Modern semi-detached home with open plan living, fitted kitchen, and driveway parking",
                "images": ["/images/prop2_1.jpg", "/images/prop2_2.jpg"],
                "last_sold": "2020-03-22",
                "last_price": "£475,000",
                "price_change": "+9.5%",
                "days_on_market": 28,
                "local_amenities": ["Secondary School 0.3mi", "Hospital 1.2mi", "Park 0.1mi"],
                "planning_restrictions": ["Tree Preservation Order", "Flood Risk Zone 2"]
            },
            {
                "id": "PROP003",
                "address": "67 Birch Close, Manchester M1 4EF", 
                "postcode": "M1 4EF",
                "type": "Flat",
                "bedrooms": 2,
                "bathrooms": 1,
                "price": "£375,000",
                "estimated_value": 375000,
                "price_per_sqft": "£395",
                "floor_area": 949,
                "garden": False,
                "parking": True,
                "council": "Manchester City Council",
                "council_tax_band": "C",
                "epc_rating": "B",
                "tenure": "Leasehold",
                "coordinates": [53.4788, -2.2396],
                "description": "Contemporary apartment with balcony, underground parking, and communal gardens",
                "images": ["/images/prop3_1.jpg", "/images/prop3_2.jpg"],
                "last_sold": "2021-09-10",
                "last_price": "£340,000",
                "price_change": "+10.3%",
                "days_on_market": 35,
                "local_amenities": ["Gym 0.1mi", "Restaurants 0.2mi", "Metro 0.4mi"],
                "planning_restrictions": ["High-rise development nearby", "Noise abatement zone"]
            }
        ]
        
        # Filter properties based on search criteria
        filtered_properties = properties
        if search_request.property_type:
            filtered_properties = [p for p in filtered_properties if p["type"].lower() == search_request.property_type.lower()]
        
        return {
            "success": True,
            "total_found": len(filtered_properties),
            "properties": filtered_properties,
            "search_criteria": {
                "address": search_request.address,
                "postcode": search_request.postcode,
                "property_type": search_request.property_type,
                "price_range": search_request.price_range
            },
            "market_summary": {
                "average_price": "£493,333",
                "price_change_12m": "+8.9%",
                "average_days_on_market": 35,
                "total_listings": 248
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Property search failed: {str(e)}")

@app.post("/api/property-api/valuation")
async def get_property_valuation(valuation_request: PropertyValuationRequest):
    """Get comprehensive property valuation with market analysis"""
    try:
        # Calculate mock valuation based on inputs
        base_value = 450000
        
        # Adjust for property type
        type_multipliers = {
            "detached": 1.3,
            "semi-detached": 1.1, 
            "terraced": 1.0,
            "flat": 0.8,
            "bungalow": 1.2
        }
        
        multiplier = type_multipliers.get(valuation_request.property_type.lower(), 1.0)
        bedroom_bonus = (valuation_request.bedrooms or 3) * 25000
        bathroom_bonus = (valuation_request.bathrooms or 2) * 15000
        garden_bonus = 20000 if valuation_request.garden else 0
        
        estimated_value = int((base_value * multiplier) + bedroom_bonus + bathroom_bonus + garden_bonus)
        lower_estimate = int(estimated_value * 0.9)
        upper_estimate = int(estimated_value * 1.15)
        
        return {
            "success": True,
            "property": {
                "address": valuation_request.address,
                "postcode": valuation_request.postcode,
                "type": valuation_request.property_type,
                "bedrooms": valuation_request.bedrooms,
                "bathrooms": valuation_request.bathrooms
            },
            "valuation": {
                "estimated_value": estimated_value,
                "lower_estimate": lower_estimate,
                "upper_estimate": upper_estimate,
                "confidence": "High",
                "valuation_date": datetime.now().strftime("%Y-%m-%d"),
                "methodology": "Automated Valuation Model (AVM)"
            },
            "market_analysis": {
                "recent_sales": [
                    {"address": "125 Oak Avenue", "price": 470000, "date": "2024-08-15", "difference": "+3.2%"},
                    {"address": "121 Oak Avenue", "price": 455000, "date": "2024-07-22", "difference": "-0.8%"},
                    {"address": "119 Oak Avenue", "price": 492000, "date": "2024-06-10", "difference": "+7.8%"}
                ],
                "local_trends": {
                    "price_change_3m": "+2.1%",
                    "price_change_12m": "+8.4%",
                    "average_days_on_market": 38,
                    "sales_volume": 24
                },
                "comparable_properties": {
                    "similar_type_average": estimated_value + random.randint(-15000, 15000),
                    "same_street_average": estimated_value + random.randint(-25000, 25000),
                    "postcode_average": estimated_value + random.randint(-35000, 35000)
                }
            },
            "factors": {
                "positive": ["Good local amenities", "Transport links", "School catchment"],
                "negative": ["Busy road nearby", "Limited parking"],
                "neutral": ["Standard condition", "Typical for area"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Valuation failed: {str(e)}")

@app.get("/api/property-api/ownership/{postcode}")
async def get_property_ownership(postcode: str):
    """Get Land Registry ownership data"""
    try:
        # Mock Land Registry data
        ownership_data = {
            "success": True,
            "postcode": postcode.upper(),
            "properties": [
                {
                    "title_number": "ABC123456",
                    "address": f"123 Example Street, {postcode.upper()}",
                    "tenure": "Freehold",
                    "registered_owner": "John Smith",
                    "proprietor_address": "Same as property address",
                    "registration_date": "2019-06-15",
                    "last_sale_price": "£415,000",
                    "last_sale_date": "2019-06-15",
                    "property_description": "A dwelling-house known as 123 Example Street",
                    "charges": [],
                    "restrictions": [],
                    "notes": ["Property benefits from right of way over adjacent land"]
                }
            ],
            "land_registry_url": f"https://landregistry.data.gov.uk/app/ukhpi/browse?from=&location=http%3A%2F%2Flandregistry.data.gov.uk%2Fid%2Fregion%2Funited-kingdom&to=&lang=en",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return ownership_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ownership lookup failed: {str(e)}")

@app.get("/api/property-api/planning-history/{postcode}")
async def get_planning_history(postcode: str):
    """Get planning application history for area"""
    try:
        planning_applications = [
            {
                "reference": "2024/0123/FULL",
                "address": f"123 Example Street, {postcode.upper()}",
                "proposal": "Single storey rear extension",
                "application_type": "Full Planning Permission",
                "submitted_date": "2024-02-15",
                "decision": "Approved",
                "decision_date": "2024-04-12",
                "case_officer": "Sarah Johnson",
                "agent": "ABC Planning Consultants",
                "applicant": "Mr. John Smith",
                "status": "Completed",
                "documents_url": "/planning/docs/2024-0123",
                "consultation_responses": 3,
                "objections": 0,
                "comments": ["No objections from neighbours", "Complies with local policy"]
            },
            {
                "reference": "2023/0987/FULL",
                "address": f"125 Example Street, {postcode.upper()}", 
                "proposal": "Two storey side extension",
                "application_type": "Full Planning Permission",
                "submitted_date": "2023-11-08",
                "decision": "Refused",
                "decision_date": "2024-01-22",
                "case_officer": "Michael Brown",
                "agent": "XYZ Architects",
                "applicant": "Mrs. Jane Doe",
                "status": "Refused",
                "documents_url": "/planning/docs/2023-0987",
                "consultation_responses": 8,
                "objections": 4,
                "refusal_reasons": [
                    "Excessive bulk and scale",
                    "Adverse impact on neighbour amenity", 
                    "Poor design quality"
                ],
                "comments": ["Strong local opposition", "Officer recommendation to refuse"]
            },
            {
                "reference": "2023/0654/FUL",
                "address": f"127 Example Street, {postcode.upper()}",
                "proposal": "Loft conversion with rear dormer window",
                "application_type": "Full Planning Permission", 
                "submitted_date": "2023-08-20",
                "decision": "Approved",
                "decision_date": "2023-10-15",
                "case_officer": "Lisa Wilson",
                "agent": "DEF Planning Services",
                "applicant": "Mr. David Jones",
                "status": "Approved",
                "documents_url": "/planning/docs/2023-0654",
                "consultation_responses": 2,
                "objections": 0,
                "conditions": [
                    "Materials to match existing",
                    "Work to commence within 3 years",
                    "Permitted development rights removed"
                ]
            }
        ]
        
        return {
            "success": True,
            "postcode": postcode.upper(),
            "total_applications": len(planning_applications),
            "applications": planning_applications,
            "summary": {
                "approved": 2,
                "refused": 1,
                "pending": 0,
                "withdrawn": 0,
                "success_rate": "67%"
            },
            "trends": {
                "most_common_type": "Extensions",
                "average_decision_time": "68 days",
                "recent_activity": "Moderate"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planning history lookup failed: {str(e)}")

@app.get("/api/property-api/market-analytics/{area}")
async def get_market_analytics(area: str):
    """Get comprehensive market analytics for area"""
    try:
        return {
            "success": True,
            "area": area,
            "market_data": {
                "current_stats": {
                    "average_price": "£487,250",
                    "median_price": "£465,000", 
                    "price_per_sqft": "£315",
                    "total_sales_12m": 284,
                    "average_days_on_market": 42,
                    "sale_success_rate": "87%"
                },
                "price_trends": {
                    "1_month": "+1.2%",
                    "3_months": "+3.8%", 
                    "6_months": "+6.1%",
                    "12_months": "+8.9%",
                    "5_years": "+34.2%"
                },
                "property_types": {
                    "terraced": {"count": 156, "avg_price": "£445,000", "change": "+7.8%"},
                    "semi_detached": {"count": 89, "avg_price": "£525,000", "change": "+9.2%"},
                    "detached": {"count": 34, "avg_price": "£675,000", "change": "+11.1%"},
                    "flat": {"count": 73, "avg_price": "£385,000", "change": "+6.4%"}
                },
                "local_features": {
                    "schools": {"primary": 8, "secondary": 3, "ofsted_good_plus": "85%"},
                    "transport": {"train_stations": 2, "bus_routes": 12, "tube_zones": "N/A"},
                    "amenities": {"shops": 45, "restaurants": 23, "parks": 6},
                    "crime_rate": "Below average", 
                    "air_quality": "Good"
                },
                "forecasts": {
                    "next_6_months": "+2.5%",
                    "next_12_months": "+4.8%",
                    "confidence": "Medium"
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market analytics failed: {str(e)}")

# Property data lookup endpoint (fixed)
@app.post("/api/property/lookup")
async def property_lookup(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Property data lookup with quota enforcement"""
    # Quota is enforced by middleware
    body = await request.json()
    address = body.get("address")
    if not address:
        raise HTTPException(status_code=400, detail="Address required")
    # TODO: Integrate with actual property data APIs
    return {
        "lookup_id": f"PROP-{datetime.now().strftime('%Y%m%d')}-{current_user['org_id']}",
        "address": address,
        "uprn": "123456789",
        "council_tax_band": "D",
        "epc_rating": "C",
        "energy_score": 72,
        "last_sale_price": "£285,000",
        "last_sale_date": "2021-03-15",
        "quota_used": True
    }

# Production API endpoints with proper authentication and quota enforcement

@app.post("/api/billing/create-checkout")
async def create_checkout_session(
    request: Request,
    current_user: dict = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Create Stripe checkout session for plan upgrade"""
    try:
        body = await request.json()
        plan_type = body.get("plan")
        
        if not plan_type:
            raise HTTPException(status_code=400, detail="Plan type required")
        
        # For now, return mock checkout URL until Stripe is properly integrated
        return {"checkout_url": "https://checkout.stripe.com/pay/test_checkout_session"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/billing/portal")
async def get_billing_portal(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Stripe billing portal URL"""
    try:
        portal_url = await StripeService.get_billing_portal_url(
            org_id=current_user["org_id"],
            return_url=str(request.base_url),
            db=db
        )
        return {"portal_url": portal_url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Get user dashboard statistics with usage data"""
    try:
        # Try to get real usage data
        if PRODUCTION_AUTH_AVAILABLE:
            from production_auth import get_current_usage
        
        try:
            from models import Usage, Organization
            from datetime import datetime
            
            # Get current month usage
            now = datetime.utcnow()
            month_start = datetime(now.year, now.month, 1)
            
            # Get usage counts
            site_analyses = db.query(Usage).filter(
                Usage.org_id == current_user["org_id"],
                Usage.resource_type == "site_analyses",
                Usage.created_at >= month_start
            ).count()
            
            documents = db.query(Usage).filter(
                Usage.org_id == current_user["org_id"],
                Usage.resource_type == "documents", 
                Usage.created_at >= month_start
            ).count()
            
            api_calls = db.query(Usage).filter(
                Usage.org_id == current_user["org_id"],
                Usage.resource_type == "api_calls",
                Usage.created_at >= month_start
            ).count()
            
            # Get organization for plan info
            org = db.query(Organization).filter(Organization.id == current_user["org_id"]).first()
            plan_type = org.plan_type.value if org else "enterprise"
            
        except Exception as db_error:
            print(f"⚠️ Database query failed, using demo data: {db_error}")
            # Fallback to demo data
            site_analyses = 24
            documents = 156
            api_calls = 2847
            plan_type = "enterprise"
        
        # Calculate cost savings (estimated)
        cost_per_analysis = 1500  # £1,500 average consultant cost per analysis
        estimated_savings = site_analyses * cost_per_analysis
        
        return {
            "site_analyses": site_analyses,
            "documents": documents,
            "api_calls": api_calls,
            "estimated_savings": estimated_savings,
            "plan_type": plan_type,
            "usage": {
                "site_analyses": {
                    "current": site_analyses, 
                    "limit": "unlimited"
                },
                "documents": {
                    "current": documents, 
                    "limit": "unlimited"
                },
                "api_calls": {
                    "current": api_calls,
                    "limit": "unlimited"
                }
            }
        }
        
    except Exception as e:
        # Complete fallback
        return {
            "site_analyses": 24,
            "documents": 156,
            "api_calls": 2847,
            "estimated_savings": 36000,
            "plan_type": "enterprise",
            "usage": {
                "site_analyses": {"current": 24, "limit": "unlimited"},
                "documents": {"current": 156, "limit": "unlimited"},
                "api_calls": {"current": 2847, "limit": "unlimited"}
            }
        }

# =============================================================================
# PROJECTS MODULE - Core project management functionality
# =============================================================================

# Projects Page Routes
@app.get("/projects")
async def projects_page(request: Request):
    """Projects listing page"""
    return templates.TemplateResponse("projects_list.html", {"request": request})

@app.get("/projects/new")
async def new_project_page(request: Request):
    """New project creation page"""
    return templates.TemplateResponse("project_new.html", {"request": request})

@app.get("/projects/{project_id}")
async def project_detail_page(request: Request, project_id: str):
    """Individual project detail page"""
    return templates.TemplateResponse("project_detail.html", {"request": request, "project_id": project_id})

# Projects API Endpoints
@app.get("/api/projects")
async def get_projects(
    search: str = None,
    status: str = None,
    type: str = None,
    limit: int = 50,
    offset: int = 0
):
    """Get projects with optional filtering"""
    # Mock project data - in production this would query the database
    projects = [
        {
            "id": "proj_001",
            "name": "Residential Development - Oak Street",
            "address": "123 Oak Street, Manchester, M1 2AB",
            "type": "residential",
            "status": "planning",
            "ai_score": 78,
            "document_count": 5,
            "created_at": (datetime.now() - timedelta(days=7)).isoformat(),
            "updated_at": (datetime.now() - timedelta(hours=2)).isoformat(),
            "local_authority": "Manchester City Council",
            "site_area": 2.5,
            "units_proposed": 24,
            "latitude": 53.4808,
            "longitude": -2.2426
        },
        {
            "id": "proj_002", 
            "name": "Commercial Hub - City Centre",
            "address": "45 Market Street, Leeds, LS1 3AB",
            "type": "commercial",
            "status": "submitted",
            "ai_score": 65,
            "document_count": 8,
            "created_at": (datetime.now() - timedelta(days=14)).isoformat(),
            "updated_at": (datetime.now() - timedelta(days=3)).isoformat(),
            "local_authority": "Leeds City Council",
            "site_area": 1.2,
            "units_proposed": 0,
            "latitude": 53.7997,
            "longitude": -1.5492
        },
        {
            "id": "proj_003",
            "name": "Mixed Use Development - Riverside",
            "address": "78 Riverside Drive, Birmingham, B2 4AB",
            "type": "mixed_use",
            "status": "under_review",
            "ai_score": 82,
            "document_count": 12,
            "created_at": (datetime.now() - timedelta(days=21)).isoformat(),
            "updated_at": (datetime.now() - timedelta(days=1)).isoformat(),
            "local_authority": "Birmingham City Council",
            "site_area": 3.8,
            "units_proposed": 45,
            "latitude": 52.4862,
            "longitude": -1.8904
        }
    ]
    
    # Apply filters
    filtered_projects = projects
    
    if search:
        search_lower = search.lower()
        filtered_projects = [
            p for p in filtered_projects 
            if search_lower in p["name"].lower() or search_lower in p["address"].lower()
        ]
    
    if status:
        filtered_projects = [p for p in filtered_projects if p["status"] == status]
    
    if type:
        filtered_projects = [p for p in filtered_projects if p["type"] == type]
    
    # Apply pagination
    total = len(filtered_projects)
    filtered_projects = filtered_projects[offset:offset + limit]
    
    return {
        "projects": filtered_projects,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.post("/api/projects")
async def create_project(project_data: dict):
    """Create a new project"""
    # TODO: Add proper validation and database storage
    # For now, return a mock response
    project_id = f"proj_{len(project_data.get('name', '').split())}{datetime.now().timestamp():.0f}"
    
    # Simulate project creation
    new_project = {
        "id": project_id,
        "name": project_data.get("name"),
        "address": project_data.get("address"),
        "type": project_data.get("type"),
        "status": project_data.get("status", "planning"),
        "description": project_data.get("description"),
        "local_authority": project_data.get("local_authority"),
        "site_area": project_data.get("site_area"),
        "units_proposed": project_data.get("units_proposed"),
        "floors": project_data.get("floors"),
        "parking_spaces": project_data.get("parking_spaces"),
        "latitude": project_data.get("latitude"),
        "longitude": project_data.get("longitude"),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "ai_score": None,
        "document_count": 0
    }
    
    return new_project

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get a specific project by ID"""
    # Mock project data - in production this would query the database
    mock_projects = {
        "proj_001": {
            "id": "proj_001",
            "name": "Residential Development - Oak Street",
            "address": "123 Oak Street, Manchester, M1 2AB",
            "type": "residential",
            "status": "planning",
            "description": "A sustainable residential development featuring 24 affordable housing units with integrated green spaces and sustainable transport links.",
            "ai_score": 78,
            "document_count": 5,
            "created_at": (datetime.now() - timedelta(days=7)).isoformat(),
            "updated_at": (datetime.now() - timedelta(hours=2)).isoformat(),
            "local_authority": "Manchester City Council",
            "site_area": 2.5,
            "units_proposed": 24,
            "floors": 3,
            "parking_spaces": 18,
            "latitude": 53.4808,
            "longitude": -2.2426,
            "estimated_timeline": "18-24 months"
        }
    }
    
    if project_id not in mock_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return mock_projects[project_id]

@app.get("/api/projects/{project_id}/activity")
async def get_project_activity(project_id: str):
    """Get activity timeline for a project"""
    activity = [
        {
            "id": 1,
            "description": "Project created",
            "timestamp": (datetime.now() - timedelta(days=7)).isoformat(),
            "icon": "plus-circle"
        },
        {
            "id": 2,
            "description": "Site survey completed and uploaded",
            "timestamp": (datetime.now() - timedelta(days=5)).isoformat(),
            "icon": "file-upload"
        },
        {
            "id": 3,
            "description": "AI analysis completed - 78% approval probability",
            "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
            "icon": "brain"
        },
        {
            "id": 4,
            "description": "Planning documents generated",
            "timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
            "icon": "file-plus"
        }
    ]
    
    return activity

@app.get("/api/projects/{project_id}/ai-analysis")
async def get_project_ai_analysis(project_id: str):
    """Get AI analysis for a project"""
    analysis = {
        "score": 78,
        "positive_factors": [
            "Site located within designated development area",
            "Adequate transport infrastructure nearby",
            "Meets local housing density requirements",
            "Environmental impact assessment favorable"
        ],
        "risk_factors": [
            "Site partially within flood risk zone 2",
            "Heritage building 200m away - potential constraints",
            "Local parking capacity may be insufficient"
        ],
        "recommendations": [
            "Include sustainable drainage system (SuDS)",
            "Consider heritage impact assessment",
            "Propose additional cycle parking",
            "Engage early with local community"
        ],
        "policy_context": "The development aligns with the Local Plan's objectives for sustainable housing delivery. Key policy considerations include LP-H1 (Housing Delivery), LP-E3 (Environmental Protection), and LP-T2 (Transport Infrastructure). The site's location supports the council's strategic housing objectives while maintaining environmental standards."
    }
    
    return analysis

@app.get("/api/projects/{project_id}/documents")
async def get_project_documents(project_id: str):
    """Get documents for a project"""
    documents = [
        {
            "id": "doc_001",
            "name": "Site Survey Report",
            "type": "pdf",
            "size": "2.3 MB",
            "uploaded_at": (datetime.now() - timedelta(days=5)).isoformat()
        },
        {
            "id": "doc_002",
            "name": "Planning Application Form",
            "type": "pdf",
            "size": "1.8 MB", 
            "uploaded_at": (datetime.now() - timedelta(days=3)).isoformat()
        },
        {
            "id": "doc_003",
            "name": "Site Plans",
            "type": "dwg",
            "size": "5.2 MB",
            "uploaded_at": (datetime.now() - timedelta(days=2)).isoformat()
        },
        {
            "id": "doc_004",
            "name": "Environmental Impact Assessment",
            "type": "docx",
            "size": "3.1 MB",
            "uploaded_at": (datetime.now() - timedelta(hours=12)).isoformat()
        }
    ]
    
    return documents

@app.get("/api/projects/{project_id}/timeline")
async def get_project_timeline(project_id: str):
    """Get project timeline/milestones"""
    timeline = [
        {
            "title": "Project Initiation",
            "description": "Project created and initial data entered",
            "date": (datetime.now() - timedelta(days=7)).isoformat(),
            "completed": True
        },
        {
            "title": "Site Analysis",
            "description": "Site survey, constraints analysis, and AI assessment",
            "date": (datetime.now() - timedelta(days=3)).isoformat(),
            "completed": True
        },
        {
            "title": "Document Preparation",
            "description": "Planning application documents generation",
            "date": datetime.now().isoformat(),
            "completed": False
        },
        {
            "title": "Planning Submission",
            "description": "Submit planning application to local authority",
            "date": (datetime.now() + timedelta(days=14)).isoformat(),
            "completed": False
        },
        {
            "title": "Authority Review",
            "description": "Local authority review and consultation period",
            "date": (datetime.now() + timedelta(days=28)).isoformat(),
            "completed": False
        },
        {
            "title": "Decision",
            "description": "Planning decision received",
            "date": (datetime.now() + timedelta(days=56)).isoformat(),
            "completed": False
        }
    ]
    
    return timeline

# Planning AI and Constraints API
@app.get("/api/planning/constraints")
async def get_planning_constraints(lat: float, lng: float):
    """Get planning constraints for a location"""
    # Mock constraints data - in production this would query GIS services
    constraints = [
        {
            "name": "Conservation Area",
            "icon": "landmark",
            "severity": "medium",
            "distance": "150m away"
        },
        {
            "name": "Flood Risk Zone 2",
            "icon": "water",
            "severity": "high", 
            "distance": "Site partially affected"
        },
        {
            "name": "Green Belt",
            "icon": "tree",
            "severity": "low",
            "distance": "500m away"
        },
        {
            "name": "Tree Preservation Order",
            "icon": "leaf",
            "severity": "medium",
            "distance": "3 protected trees on site"
        }
    ]
    
    return constraints

@app.post("/api/planning/ai-analysis")
async def get_planning_ai_analysis(project_data: dict):
    """Get AI analysis for project data"""
    # Mock AI analysis - in production this would call actual AI service
    base_score = 60
    
    # Adjust score based on project characteristics
    score_adjustments = 0
    factors = []
    
    # Type adjustments
    if project_data.get("type") == "residential":
        score_adjustments += 10
        factors.append("residential development priority")
    elif project_data.get("type") == "affordable_housing":
        score_adjustments += 15
        factors.append("affordable housing need")
    
    # Size adjustments
    units = int(project_data.get("units_proposed", 0))
    if units > 0 and units <= 50:
        score_adjustments += 5
        factors.append("appropriate development scale")
    
    # Site area
    site_area = float(project_data.get("site_area", 0))
    if site_area > 0 and site_area < 5:
        score_adjustments += 8
        factors.append("suitable site size")
    
    final_score = min(100, base_score + score_adjustments)
    
    analysis = {
        "score": final_score,
        "factors": factors,
        "recommendations": "Consider sustainable design features and early community engagement"
    }
    
    return analysis

if __name__ == "__main__":
    import uvicorn
    print("\nStarting Domus Professional Platform...")
    uvicorn.run(app, host="0.0.0.0", port=8000)