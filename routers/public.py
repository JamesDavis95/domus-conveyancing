"""
Public routes for Domus
Handles home page, pricing, security, contact forms
"""

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database_config import get_db
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/old-home", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the old home page (moved from / to avoid conflicts)"""
    static_build_id = getattr(request.app.state, 'static_build_id', 'dev')
    
    response = templates.TemplateResponse("pages/home.html", {
        "request": request,
        "static_build_id": static_build_id
    })
    response.headers["Cache-Control"] = "no-store"
    return response

@router.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    """Serve pricing page"""
    static_build_id = getattr(request.app.state, 'static_build_id', 'dev')
    
    response = templates.TemplateResponse("pages/pricing.html", {
        "request": request,
        "static_build_id": static_build_id
    })
    response.headers["Cache-Control"] = "no-store"
    return response

@router.get("/security", response_class=HTMLResponse)
async def security(request: Request):
    """Serve security page"""
    static_build_id = getattr(request.app.state, 'static_build_id', 'dev')
    
    response = templates.TemplateResponse("pages/security.html", {
        "request": request,
        "static_build_id": static_build_id
    })
    response.headers["Cache-Control"] = "no-store"
    return response

@router.get("/contact", response_class=HTMLResponse)
async def contact_form(request: Request):
    """Serve contact form"""
    static_build_id = getattr(request.app.state, 'static_build_id', 'dev')
    
    response = templates.TemplateResponse("pages/contact.html", {
        "request": request,
        "static_build_id": static_build_id
    })
    response.headers["Cache-Control"] = "no-store"
    return response

@router.post("/contact")
async def submit_contact(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle contact form submission"""
    try:
        # TODO: Implement email sending via lib/emails.py
        # For now, just return success
        return RedirectResponse(url="/contact?success=1", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send message")