"""
Compliance API Endpoints
FastAPI endpoints for serving compliance documentation
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Optional
import markdown
from datetime import datetime

from lib.compliance import compliance_manager

router = APIRouter(prefix="/api/compliance", tags=["compliance"])

@router.get("/documents")
async def list_compliance_documents():
    """List all available compliance documents"""
    
    return {
        "status": "success",
        "documents": compliance_manager.get_document_summary()
    }

@router.get("/privacy-policy")
async def get_privacy_policy(
    format: str = Query("html", description="Response format: html, markdown, json")
):
    """Get privacy policy in requested format"""
    
    try:
        content = compliance_manager.get_document("privacy_policy")
        
        if format == "markdown":
            return {"status": "success", "content": content, "format": "markdown"}
        elif format == "html":
            html_content = markdown.markdown(content)
            return HTMLResponse(content=html_content)
        elif format == "json":
            return {"status": "success", "content": content, "format": "json"}
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use: html, markdown, json")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving privacy policy: {str(e)}")

@router.get("/terms-of-service")
async def get_terms_of_service(
    format: str = Query("html", description="Response format: html, markdown, json")
):
    """Get terms of service in requested format"""
    
    try:
        content = compliance_manager.get_document("terms_of_service")
        
        if format == "markdown":
            return {"status": "success", "content": content, "format": "markdown"}
        elif format == "html":
            html_content = markdown.markdown(content)
            return HTMLResponse(content=html_content)
        elif format == "json":
            return {"status": "success", "content": content, "format": "json"}
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use: html, markdown, json")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving terms of service: {str(e)}")

@router.get("/cookie-policy")
async def get_cookie_policy(
    format: str = Query("html", description="Response format: html, markdown, json")
):
    """Get cookie policy in requested format"""
    
    try:
        content = compliance_manager.get_document("cookie_policy")
        
        if format == "markdown":
            return {"status": "success", "content": content, "format": "markdown"}
        elif format == "html":
            html_content = markdown.markdown(content)
            return HTMLResponse(content=html_content)
        elif format == "json":
            return {"status": "success", "content": content, "format": "json"}
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use: html, markdown, json")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving cookie policy: {str(e)}")

@router.get("/data-retention")
async def get_data_retention_schedule(
    format: str = Query("html", description="Response format: html, markdown, json")
):
    """Get data retention schedule in requested format"""
    
    try:
        content = compliance_manager.get_document("data_retention_schedule")
        
        if format == "markdown":
            return {"status": "success", "content": content, "format": "markdown"}
        elif format == "html":
            html_content = markdown.markdown(content)
            return HTMLResponse(content=html_content)
        elif format == "json":
            return {"status": "success", "content": content, "format": "json"}
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use: html, markdown, json")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving data retention schedule: {str(e)}")

@router.get("/gdpr-compliance")
async def get_gdpr_compliance_guide(
    format: str = Query("html", description="Response format: html, markdown, json")
):
    """Get GDPR compliance guide in requested format"""
    
    try:
        content = compliance_manager.get_document("gdpr_compliance")
        
        if format == "markdown":
            return {"status": "success", "content": content, "format": "markdown"}
        elif format == "html":
            html_content = markdown.markdown(content)
            return HTMLResponse(content=html_content)
        elif format == "json":
            return {"status": "success", "content": content, "format": "json"}
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use: html, markdown, json")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving GDPR compliance guide: {str(e)}")

@router.get("/compliance-status")
async def get_compliance_status():
    """Get overall compliance status and metrics"""
    
    return {
        "status": "success",
        "compliance_status": {
            "gdpr_compliant": True,
            "sra_compliant": True,
            "last_assessment": "2024-07-01",
            "next_review": "2025-07-01",
            "compliance_score": 98.5,
            "certifications": [
                "ISO 27001 (Security)",
                "SRA Authorised",
                "ICO Registered"
            ],
            "last_updated": datetime.now().isoformat(),
            "documents": {
                "privacy_policy": {"status": "current", "last_updated": "2024-10-04"},
                "terms_of_service": {"status": "current", "last_updated": "2024-10-04"},
                "cookie_policy": {"status": "current", "last_updated": "2024-10-04"},
                "data_retention_schedule": {"status": "current", "last_updated": "2024-10-04"},
                "gdpr_compliance": {"status": "current", "last_updated": "2024-10-04"}
            }
        }
    }

@router.post("/data-subject-request")
async def submit_data_subject_request(
    request_type: str,
    email: str,
    message: str,
    full_name: Optional[str] = None
):
    """Submit a data subject rights request"""
    
    valid_request_types = [
        "access", "rectification", "erasure", "restriction", 
        "portability", "objection", "complaint"
    ]
    
    if request_type not in valid_request_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid request type. Must be one of: {', '.join(valid_request_types)}"
        )
    
    # In a real implementation, this would:
    # 1. Validate the email against existing data subjects
    # 2. Create a request ticket in the system
    # 3. Send confirmation email to the requester
    # 4. Notify the DPO/privacy team
    # 5. Start the processing workflow
    
    request_id = f"DSR-{datetime.now().strftime('%Y%m%d')}-{abs(hash(email))%10000:04d}"
    
    return {
        "status": "success",
        "message": "Data subject request submitted successfully",
        "request_id": request_id,
        "request_type": request_type,
        "expected_response_time": "1 month",
        "next_steps": [
            "You will receive an email confirmation within 24 hours",
            "We may contact you to verify your identity",
            "We will process your request within 1 month",
            "You will receive the outcome via email"
        ],
        "contact_info": {
            "email": "dpo@domusconveyancing.co.uk",
            "phone": "020 1234 5678"
        }
    }

@router.get("/consent-preferences")
async def get_consent_preferences():
    """Get available consent preferences"""
    
    return {
        "status": "success",
        "consent_categories": {
            "essential": {
                "name": "Essential Cookies",
                "description": "Required for platform functionality",
                "required": True,
                "enabled": True
            },
            "analytics": {
                "name": "Analytics Cookies",
                "description": "Help us improve our services",
                "required": False,
                "enabled": False
            },
            "marketing": {
                "name": "Marketing Communications",
                "description": "Receive updates about our services",
                "required": False,
                "enabled": False
            },
            "third_party": {
                "name": "Third-Party Integrations",
                "description": "Enable enhanced platform features",
                "required": False,
                "enabled": False
            }
        }
    }

@router.post("/consent-preferences")
async def update_consent_preferences(
    essential: bool = True,
    analytics: bool = False,
    marketing: bool = False,
    third_party: bool = False
):
    """Update user consent preferences"""
    
    # In a real implementation, this would:
    # 1. Authenticate the user
    # 2. Update consent preferences in the database
    # 3. Apply changes to data processing
    # 4. Send confirmation email
    
    preferences = {
        "essential": essential,  # Always true
        "analytics": analytics,
        "marketing": marketing,
        "third_party": third_party
    }
    
    return {
        "status": "success",
        "message": "Consent preferences updated successfully",
        "preferences": preferences,
        "updated_at": datetime.now().isoformat()
    }