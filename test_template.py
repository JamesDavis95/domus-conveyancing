"""
Simple test route to debug template issues
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/test", response_class=HTMLResponse)
async def test_template(request: Request):
    """Simple test route that doesn't require auth"""
    return templates.TemplateResponse("pages/home.html", {
        "request": request,
        "static_build_id": "test"
    })