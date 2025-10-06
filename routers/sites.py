"""
Sites router for Domus AI Platform - Site management and analysis
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database_config import get_db
from lib.permissions import require_auth, require_permission, AuthContext
from models import Site, Analysis, User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/sites", response_class=HTMLResponse, dependencies=[Depends(require_permission("sites:read"))])
async def sites_list(request: Request, auth_ctx: AuthContext = Depends(require_auth)):
    """List all sites for the organization"""
    static_build_id = getattr(request.app.state, 'static_build_id', 'dev')
    
    return templates.TemplateResponse("sites_list.html", {
        "request": request,
        "title": "Sites - Domus AI",
        "static_build_id": static_build_id,
        "user_name": auth_ctx.user.email if hasattr(auth_ctx.user, 'email') else "User",
        "org_name": auth_ctx.org.name if hasattr(auth_ctx.org, 'name') else "Organization",
        "user_role": auth_ctx.membership.role if hasattr(auth_ctx.membership, 'role') else "Manager"
    })

@router.get("/sites/new", response_class=HTMLResponse, dependencies=[Depends(require_permission("sites:create"))])
async def sites_new(request: Request, auth_ctx: AuthContext = Depends(require_auth)):
    """Create new site form"""
    static_build_id = getattr(request.app.state, 'static_build_id', 'dev')
    
    return templates.TemplateResponse("sites_new.html", {
        "request": request,
        "title": "New Site - Domus AI",
        "static_build_id": static_build_id,
        "user_name": auth_ctx.user.email if hasattr(auth_ctx.user, 'email') else "User",
        "org_name": auth_ctx.org.name if hasattr(auth_ctx.org, 'name') else "Organization",
        "user_role": auth_ctx.membership.role if hasattr(auth_ctx.membership, 'role') else "Manager"
    })

@router.get("/sites/{site_id}", response_class=HTMLResponse, dependencies=[Depends(require_permission("sites:read"))])
async def sites_detail(site_id: int, request: Request, auth_ctx: AuthContext = Depends(require_auth)):
    """Site detail view"""
    static_build_id = getattr(request.app.state, 'static_build_id', 'dev')
    
    return templates.TemplateResponse("sites_detail.html", {
        "request": request,
        "title": f"Site {site_id} - Domus AI",
        "static_build_id": static_build_id,
        "site_id": site_id,
        "user_name": auth_ctx.user.email if hasattr(auth_ctx.user, 'email') else "User",
        "org_name": auth_ctx.org.name if hasattr(auth_ctx.org, 'name') else "Organization",
        "user_role": auth_ctx.membership.role if hasattr(auth_ctx.membership, 'role') else "Manager"
    })

# API Routes
@router.get("/api/sites", dependencies=[Depends(require_permission("sites:read"))])
async def api_sites_list(
    auth_ctx: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get sites list for organization"""
    try:
        sites = db.query(Site).filter(
            Site.org_id == auth_ctx.org.id
        ).order_by(Site.created_at.desc()).all()
        
        return {
            "sites": [
                {
                    "id": site.id,
                    "name": site.name,
                    "address": site.address,
                    "status": site.status,
                    "ai_score": site.ai_score,
                    "created_at": site.created_at.isoformat() if site.created_at else None,
                    "updated_at": site.updated_at.isoformat() if site.updated_at else None
                }
                for site in sites
            ]
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to fetch sites", "detail": str(e)}
        )

@router.post("/api/sites", dependencies=[Depends(require_permission("sites:create"))])
async def api_sites_create(
    request: Request,
    auth_ctx: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create a new site"""
    try:
        data = await request.json()
        
        site = Site(
            name=data.get("name"),
            address=data.get("address"),
            org_id=auth_ctx.org.id,
            created_by=auth_ctx.user.id,
            status="draft"
        )
        
        db.add(site)
        db.commit()
        db.refresh(site)
        
        return {
            "id": site.id,
            "name": site.name,
            "address": site.address,
            "status": site.status,
            "created_at": site.created_at.isoformat() if site.created_at else None
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to create site", "detail": str(e)}
        )