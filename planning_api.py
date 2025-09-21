"""
Domus Planning Platform - Main API Routes
Integrated Planning Services: Planning Applications, Building Control, Land Charges, Regulatory Services
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
import uuid

from planning_schemas import (
    PlanningApplication, 
    BuildingApplication, 
    LLC1, 
    WasteApplication, 
    PrivateHousingCase,
    IntegratedCase,
    PolicyCompliance,
    ApplicationStatus
)

router = APIRouter(prefix="/api/v1", tags=["Planning Platform"])

# ==================== PLANNING APPLICATIONS ====================

@router.post("/planning/applications")
async def create_planning_application(
    application_type: str = Form(...),
    property_address: str = Form(...),
    description: str = Form(...),
    applicant_name: str = Form(...),
    applicant_email: str = Form(None),
    documents: List[UploadFile] = File(...)
):
    """Create new planning application with document upload"""
    
    app_ref = f"25/{datetime.now().strftime('%m%d')}/{len(documents):03d}"
    
    # Process uploaded documents with AI
    doc_analysis = []
    for doc in documents:
        # AI document processing would happen here
        doc_analysis.append({
            "filename": doc.filename,
            "analysis": "AI policy compliance analysis completed",
            "compliance_score": 0.87
        })
    
    application = {
        "application_ref": app_ref,
        "application_type": application_type,
        "property_address": property_address,
        "description": description,
        "status": "Received",
        "received_date": datetime.now(),
        "documents": doc_analysis
    }
    
    return {
        "success": True,
        "application": application,
        "next_steps": ["Validation", "Policy Compliance Check", "Public Consultation"]
    }

@router.get("/planning/applications/{app_ref}")
async def get_planning_application(app_ref: str):
    """Get detailed planning application information"""
    
    # Mock data - would come from database
    return {
        "application": {
            "application_ref": app_ref,
            "property_address": "123 High Street, Hertford",
            "status": "Under Consideration",
            "case_officer": "Sarah Johnson",
            "policy_assessments": [
                {
                    "policy_reference": "LP1",
                    "policy_title": "Sustainable Development",
                    "compliance_status": "Compliant",
                    "confidence_score": 0.94
                },
                {
                    "policy_reference": "LP15", 
                    "policy_title": "Historic Environment",
                    "compliance_status": "Requires Assessment",
                    "confidence_score": 0.67
                }
            ]
        }
    }

@router.post("/planning/applications/{app_ref}/policy-check")
async def run_policy_compliance_check(app_ref: str):
    """Run AI-powered policy compliance analysis"""
    
    # This would integrate with the policy engine
    compliance_results = {
        "overall_compliance": "Mostly Compliant",
        "compliance_score": 0.85,
        "policy_checks": [
            {
                "policy": "LP1 - Sustainable Development",
                "status": "Compliant",
                "evidence": "Design statement demonstrates sustainability measures"
            },
            {
                "policy": "LP15 - Historic Environment",
                "status": "Requires Review", 
                "evidence": "Property within conservation area - heritage assessment needed"
            }
        ],
        "recommendation": "Approve with conditions",
        "estimated_decision_time": "5-7 working days"
    }
    
    return compliance_results

# ==================== BUILDING CONTROL ====================

@router.post("/building-control/applications")
async def create_building_application(
    property_address: str = Form(...),
    work_description: str = Form(...),
    application_type: str = Form("Full Plans"),
    plans: List[UploadFile] = File(...)
):
    """Create new building control application"""
    
    bc_ref = f"BC/25/{datetime.now().strftime('%m%d')}"
    
    return {
        "success": True,
        "application_ref": bc_ref,
        "status": "Received",
        "next_steps": ["Plan Check", "Site Inspection Scheduling"]
    }

# ==================== LAND CHARGES ====================

@router.get("/land-charges/search/{uprn}")
async def land_charges_search(uprn: str):
    """Perform LLC1 search for property"""
    
    # Mock LLC1 data
    charges = [
        {
            "charge_type": "Planning Application",
            "reference": "25/00123/FUL", 
            "date": "2025-03-15",
            "description": "Single storey extension"
        },
        {
            "charge_type": "Building Regulations",
            "reference": "BC/25/0456",
            "date": "2025-03-20", 
            "description": "Building control approval"
        }
    ]
    
    return {
        "uprn": uprn,
        "search_date": datetime.now(),
        "charges": charges,
        "total_charges": len(charges)
    }

# ==================== INTEGRATED SERVICES ====================

@router.get("/integrated/property/{uprn}")
async def get_integrated_property_view(uprn: str):
    """Get unified view across all services for a property"""
    
    integrated_data = {
        "uprn": uprn,
        "property_address": "123 High Street, Hertford",
        "planning_applications": [
            {"ref": "25/00123/FUL", "status": "Approved", "date": "2025-03-15"}
        ],
        "building_applications": [
            {"ref": "BC/25/0456", "status": "Approved", "date": "2025-03-20"}
        ],
        "land_charges": [
            {"type": "Planning Permission", "active": True}
        ],
        "regulatory_cases": [],
        "compliance_overview": {
            "overall_status": "Compliant",
            "last_updated": datetime.now()
        }
    }
    
    return integrated_data

# ==================== AI & ANALYTICS ====================

@router.post("/ai/analyze-application")
async def ai_analyze_application(
    app_ref: str,
    document_id: Optional[str] = None
):
    """AI analysis of planning application for policy compliance"""
    
    analysis = {
        "application_ref": app_ref,
        "ai_analysis": {
            "processing_time": "2.3 seconds",
            "confidence_score": 0.89,
            "policy_compliance": {
                "compliant_policies": 8,
                "flagged_policies": 2,
                "requires_review": 1
            },
            "risk_assessment": {
                "overall_risk": "Low",
                "factors": ["Standard householder extension", "No heritage constraints"]
            },
            "recommendation": {
                "decision": "Delegate approval",
                "conditions": ["Standard construction hours", "Materials to match existing"]
            }
        }
    }
    
    return analysis

@router.get("/analytics/dashboard")
async def get_planning_analytics():
    """Get planning department performance analytics"""
    
    return {
        "performance_metrics": {
            "applications_this_month": 156,
            "average_decision_time": "5.2 days",
            "policy_compliance_rate": "92%",
            "officer_productivity": "+15% vs last month"
        },
        "application_breakdown": {
            "householder": 67,
            "full_planning": 34,
            "outline": 12,
            "other": 43
        },
        "decision_outcomes": {
            "approved": 142,
            "refused": 8,
            "withdrawn": 6
        }
    }

# Export the router
planning_router = router