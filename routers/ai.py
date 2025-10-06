"""
AI Analysis router for Domus AI Platform
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database_config import get_db
from lib.permissions import require_auth, require_permission, AuthContext
from models import Site, Analysis

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/ai", response_class=HTMLResponse, dependencies=[Depends(require_permission("ai:analyze"))])
async def ai_dashboard(request: Request, auth_ctx: AuthContext = Depends(require_auth)):
    """AI Analysis dashboard"""
    static_build_id = getattr(request.app.state, 'static_build_id', 'dev')
    
    return templates.TemplateResponse("ai_dashboard.html", {
        "request": request,
        "title": "AI Analysis - Domus AI",
        "static_build_id": static_build_id,
        "user_name": auth_ctx.user.email if hasattr(auth_ctx.user, 'email') else "User",
        "org_name": auth_ctx.org.name if hasattr(auth_ctx.org, 'name') else "Organization",
        "user_role": auth_ctx.membership.role if hasattr(auth_ctx.membership, 'role') else "Manager"
    })

@router.get("/calculator", response_class=HTMLResponse, dependencies=[Depends(require_permission("calc:run"))])
async def calculator(request: Request, auth_ctx: AuthContext = Depends(require_auth)):
    """Development Calculator"""
    static_build_id = getattr(request.app.state, 'static_build_id', 'dev')
    
    return templates.TemplateResponse("calculator.html", {
        "request": request,
        "title": "Development Calculator - Domus AI",
        "static_build_id": static_build_id,
        "user_name": auth_ctx.user.email if hasattr(auth_ctx.user, 'email') else "User",
        "org_name": auth_ctx.org.name if hasattr(auth_ctx.org, 'name') else "Organization",
        "user_role": auth_ctx.membership.role if hasattr(auth_ctx.membership, 'role') else "Manager"
    })

@router.get("/documents", response_class=HTMLResponse, dependencies=[Depends(require_permission("docs:read"))])
async def documents(request: Request, auth_ctx: AuthContext = Depends(require_auth)):
    """Documents dashboard"""
    static_build_id = getattr(request.app.state, 'static_build_id', 'dev')
    
    return templates.TemplateResponse("documents.html", {
        "request": request,
        "title": "Documents - Domus AI",
        "static_build_id": static_build_id,
        "user_name": auth_ctx.user.email if hasattr(auth_ctx.user, 'email') else "User",
        "org_name": auth_ctx.org.name if hasattr(auth_ctx.org, 'name') else "Organization",
        "user_role": auth_ctx.membership.role if hasattr(auth_ctx.membership, 'role') else "Manager"
    })

# API Routes
@router.post("/api/ai/analyze", dependencies=[Depends(require_permission("ai:analyze"))])
async def api_analyze_site(
    request: Request,
    auth_ctx: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Run AI analysis on a site"""
    try:
        data = await request.json()
        site_id = data.get("site_id")
        
        if not site_id:
            return JSONResponse(
                status_code=400,
                content={"error": "site_id is required"}
            )
        
        # Mock AI analysis for now
        analysis = Analysis(
            site_id=site_id,
            analysis_type="viability",
            result_data={
                "score": 85,
                "confidence": 0.92,
                "factors": {
                    "location": 90,
                    "planning_history": 80,
                    "market_conditions": 85,
                    "infrastructure": 88
                },
                "recommendations": [
                    "Strong development potential",
                    "Consider mixed-use development",
                    "Check flood risk zones"
                ]
            },
            created_by=auth_ctx.user.id
        )
        
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        return {
            "id": analysis.id,
            "site_id": site_id,
            "score": 85,
            "confidence": 0.92,
            "analysis_type": "viability",
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to analyze site", "detail": str(e)}
        )