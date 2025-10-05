"""
Dashboard routes and APIs
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database_config import get_db
from lib.permissions import require_auth, require_permission, AuthContext
from models import Case, User, Membership, AuditLog

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard", response_class=HTMLResponse, dependencies=[Depends(require_auth)])
async def dashboard(request: Request, auth_ctx: AuthContext = Depends(require_auth)):
    """Serve dashboard page"""
    static_build_id = getattr(request.app.state, 'static_build_id', 'dev')
    
    response = templates.TemplateResponse("app/dashboard.html", {
        "request": request,
        "static_build_id": static_build_id,
        "auth_ctx": auth_ctx
    })
    response.headers["Cache-Control"] = "no-store"
    return response

@router.get("/api/dashboard/kpis", dependencies=[Depends(require_permission("org:read"))])
async def get_dashboard_kpis(
    auth_ctx: AuthContext = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get dashboard KPIs"""
    try:
        # Active cases count
        active_cases = db.query(Case).filter(
            Case.org_id == auth_ctx.org.id,
            Case.status.in_(["planning", "submitted"])
        ).count()
        
        # Completed cases this month  
        from datetime import datetime, timedelta
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        completed_this_month = db.query(Case).filter(
            Case.org_id == auth_ctx.org.id,
            Case.status == "approved",
            Case.updated_at >= month_start
        ).count()
        
        # Team members count
        team_members = db.query(Membership).filter(
            Membership.org_id == auth_ctx.org.id
        ).count()
        
        # Pending documents (placeholder)
        pending_documents = 0
        
        return JSONResponse({
            "active_cases": active_cases,
            "completed_this_month": completed_this_month,
            "pending_documents": pending_documents,
            "team_members": team_members
        })
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)