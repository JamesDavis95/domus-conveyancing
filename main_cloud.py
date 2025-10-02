from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from pathlib import Path
import os

# Startup verification
print("🚀 Starting Domus Planning Platform - Cloud Optimized...")
print("   Version: 4.0.0-cloud")
print("   File: main.py")
print("   Mode: Production with cloud optimizations")

# Initialize FastAPI application
app = FastAPI(
    title="Domus Planning Platform",
    description="AI-powered planning intelligence system with BNG marketplace",
    version="4.0.0-cloud",
    docs_url="/admin/docs",
    redoc_url="/admin/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Simplified for cloud deployment
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"]
)

# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "platform": "Domus Planning Platform",
        "version": "4.0.0-cloud",
        "file": "main.py",
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "authentication": "enabled",
            "bng_marketplace": "operational", 
            "ai_planning": "active",
            "user_roles": "configured"
        }
    }

@app.get("/test")
async def test_deployment():
    """Test endpoint"""
    return {
        "message": "✅ CLOUD DEPLOYMENT SUCCESS",
        "platform": "Domus Planning Platform",
        "timestamp": datetime.utcnow().isoformat()
    }

# User Management System
users_db = {
    "super_admin": {
        "username": "super_admin",
        "email": "admin@domusplanning.co.uk",
        "role": "super_admin",
        "permissions": ["all"],
        "created": datetime.utcnow().isoformat()
    },
    "planner": {
        "username": "planner", 
        "email": "planner@domusplanning.co.uk",
        "role": "planner",
        "permissions": ["planning", "documents", "consultations"],
        "created": datetime.utcnow().isoformat()
    },
    "council": {
        "username": "council",
        "email": "council@domusplanning.co.uk", 
        "role": "council",
        "permissions": ["validation", "approvals", "compliance"],
        "created": datetime.utcnow().isoformat()
    }
}

@app.get("/api/users")
async def list_users():
    """List all users with roles and permissions"""
    return {
        "users": list(users_db.values()),
        "total": len(users_db),
        "roles": ["super_admin", "planner", "council", "developer", "resident"]
    }

@app.get("/api/roles")
async def get_roles():
    """Get role definitions and permissions"""
    return {
        "roles": {
            "super_admin": {
                "name": "Super Administrator",
                "permissions": ["all"],
                "description": "Full system access and control"
            },
            "planner": {
                "name": "Planning Professional", 
                "permissions": ["planning", "documents", "consultations"],
                "description": "Planning application management and consultation"
            },
            "council": {
                "name": "Council Officer",
                "permissions": ["validation", "approvals", "compliance"],
                "description": "Application validation and approval workflow"
            },
            "developer": {
                "name": "Developer",
                "permissions": ["submit", "track", "documents"],
                "description": "Submit and track planning applications"
            },
            "resident": {
                "name": "Resident",
                "permissions": ["view", "comment", "object"],
                "description": "View applications and submit objections"
            }
        }
    }

# BNG Marketplace
bng_listings = [
    {
        "id": "BNG001",
        "title": "Premium Woodland Biodiversity Credits",
        "location": "Oxfordshire",
        "area_hectares": 15.5,
        "biodiversity_units": 180,
        "unit_price": 25000,
        "total_value": 4500000,
        "habitat_type": "Deciduous Woodland",
        "status": "available",
        "seller": "Green Estate Management Ltd",
        "certification": "Natural England Approved",
        "delivery_timeline": "Q2 2025"
    },
    {
        "id": "BNG002", 
        "title": "Grassland Habitat Enhancement Project",
        "location": "Devon",
        "area_hectares": 42.8,
        "biodiversity_units": 312,
        "unit_price": 18500,
        "total_value": 5772000,
        "habitat_type": "Species-rich Grassland",
        "status": "available",
        "seller": "Southwest Conservation Trust",
        "certification": "Natural England Approved",
        "delivery_timeline": "Q3 2025"
    }
]

@app.get("/api/bng/marketplace")
async def bng_marketplace():
    """BNG Marketplace listings"""
    return {
        "listings": bng_listings,
        "total_listings": len(bng_listings),
        "total_units_available": sum(listing["biodiversity_units"] for listing in bng_listings),
        "marketplace_status": "operational"
    }

@app.get("/api/bng/listing/{listing_id}")
async def get_bng_listing(listing_id: str):
    """Get specific BNG listing details"""
    listing = next((l for l in bng_listings if l["id"] == listing_id), None)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing

# Main application interface
@app.get("/")
async def root():
    """Serve the complete production platform interface"""
    frontend_path = Path("frontend/platform_clean.html")
    
    if frontend_path.exists():
        with open(frontend_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content)
    else:
        # If frontend file doesn't exist, return error
        raise HTTPException(status_code=404, detail="Platform interface not found")

# Complete user role system from our production build
@app.get("/api/users")
async def list_users():
    """List all users with comprehensive role system"""
    production_users = {
        "super_admin": {
            "username": "super_admin",
            "email": "admin@domusplanning.co.uk",
            "role": "super_admin",
            "permissions": ["all"],
            "plan": "enterprise",
            "created": datetime.utcnow().isoformat(),
            "status": "active"
        },
        "developer_001": {
            "username": "developer_001",
            "email": "developer@domusplanning.co.uk",
            "role": "developer", 
            "permissions": ["planning_ai", "auto_docs", "property_api", "bng_marketplace_buy"],
            "plan": "professional",
            "created": datetime.utcnow().isoformat(),
            "status": "active"
        },
        "consultant_001": {
            "username": "consultant_001",
            "email": "consultant@domusplanning.co.uk",
            "role": "consultant",
            "permissions": ["planning_ai", "auto_docs", "property_api", "team_workspace", "bng_marketplace_buy"],
            "plan": "professional", 
            "created": datetime.utcnow().isoformat(),
            "status": "active"
        },
        "landowner_001": {
            "username": "landowner_001", 
            "email": "landowner@domusplanning.co.uk",
            "role": "landowner",
            "permissions": ["bng_marketplace_sell", "land_portfolio"],
            "plan": "core",
            "created": datetime.utcnow().isoformat(),
            "status": "active"
        },
        "authority_001": {
            "username": "authority_001",
            "email": "authority@localcouncil.gov.uk", 
            "role": "authority",
            "permissions": ["application_review", "policy_compliance", "local_development"],
            "plan": "enterprise",
            "created": datetime.utcnow().isoformat(),
            "status": "active"
        }
    }
    
    return {
        "users": list(production_users.values()),
        "total": len(production_users),
        "roles": ["super_admin", "developer", "consultant", "landowner", "authority"],
        "plans": ["core", "professional", "enterprise"]
    }

@app.get("/api/roles")
async def get_roles():
    """Get comprehensive role definitions and permissions"""
    return {
        "roles": {
            "super_admin": {
                "name": "Super Administrator",
                "permissions": ["all"],
                "description": "Complete platform administration with user management and permission controls",
                "features": ["admin_panel", "user_management", "billing_management", "platform_administration"]
            },
            "developer": {
                "name": "Developer/Promoter", 
                "permissions": ["planning_ai", "auto_docs", "property_api", "bng_marketplace_buy"],
                "description": "Streamline planning applications and development workflows with AI-powered insights",
                "features": ["projects", "planning_ai", "auto_docs", "property_api"]
            },
            "consultant": {
                "name": "Planning Consultant",
                "permissions": ["planning_ai", "auto_docs", "property_api", "team_workspace", "bng_marketplace_buy"],
                "description": "Professional planning consultancy toolkit with client collaboration features", 
                "features": ["projects", "planning_ai", "auto_docs", "property_api", "team_workspace"]
            },
            "landowner": {
                "name": "Landowner",
                "permissions": ["bng_marketplace_sell", "land_portfolio", "offset_contracts"],
                "description": "Maximize your land asset value with planning intelligence and offset opportunities",
                "features": ["marketplace", "land_portfolio", "offset_contracts"]
            },
            "authority": {
                "name": "Planning Authority",
                "permissions": ["application_review", "policy_compliance", "local_development"],
                "description": "Efficient application processing and policy compliance management tools",
                "features": ["application_review", "policy_compliance", "local_development"]
            }
        },
        "permissions": {
            "planning_ai": "Access to AI-powered planning analysis and site assessments",
            "auto_docs": "Automated document generation for planning applications", 
            "property_api": "Comprehensive property data and planning intelligence",
            "bng_marketplace_buy": "Purchase biodiversity net gain credits",
            "bng_marketplace_sell": "List and sell biodiversity net gain credits",
            "team_workspace": "Collaborate with team members and clients",
            "admin_panel": "Platform administration and user management",
            "application_review": "Review and process planning applications",
            "policy_compliance": "Monitor policy compliance and regulatory changes"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))