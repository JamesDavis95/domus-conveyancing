"""
Comprehensive Regulatory Services API
Supporting full council tender requirements: Planning, Building Control, Land Charges, Waste, Housing
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
import random
import uuid

from regulatory_schemas import (
    # Planning
    PlanningApplication, PlanningApplicationType, PlanningStatus,
    # Building Control
    BuildingControlApplication, BuildingControlType, BuildingControlStage,
    # Land Charges
    LandChargesSearch, LandChargesSearchType, LandChargesStatus,
    # Waste Regulatory
    WasteRegulatoryCase, WasteLicenceType, WasteComplianceStatus,
    # Private Housing
    PrivateHousingCase, HousingEnforcementType, HousingComplianceStatus,
    # Integrated
    IntegratedRegulatoryCase, CaseType, CasePriority,
    # User Management
    UserPermissions, UserRole, Department,
    # Audit
    AuditEntry, AuditAction
)

# Initialize FastAPI app
regulatory_app = FastAPI(
    title="Domus Regulatory Platform API",
    description="Comprehensive regulatory services for local councils",
    version="2.0.0"
)

# ============================================================================
# PLANNING APPLICATIONS API
# ============================================================================

@regulatory_app.get("/api/planning/applications")
async def get_planning_applications(
    status: Optional[PlanningStatus] = None,
    officer: Optional[str] = None,
    ward: Optional[str] = None,
    limit: int = Query(50, le=200)
):
    """Get planning applications with filtering"""
    # Generate sample data
    applications = []
    statuses = list(PlanningStatus) if not status else [status]
    officers = ["Sarah Johnson", "Mike Peters", "Emma Wilson", "David Clark"] if not officer else [officer]
    wards = ["Central", "North", "South", "East", "West"] if not ward else [ward]
    
    for i in range(min(limit, 25)):
        app_date = datetime.now() - timedelta(days=random.randint(1, 180))
        target_date = app_date + timedelta(weeks=8)
        
        application = {
            "id": f"24/{random.randint(1000, 9999):04d}",
            "application_type": random.choice(list(PlanningApplicationType)).value,
            "status": random.choice(statuses).value,
            "site_address": f"{random.randint(1, 999)} {random.choice(['High Street', 'Church Lane', 'Mill Road', 'Victoria Avenue', 'King Street'])}, {random.choice(wards)} Ward",
            "applicant_name": f"{random.choice(['John', 'Jane', 'David', 'Sarah', 'Michael'])} {random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones'])}",
            "description": random.choice([
                "Single storey rear extension",
                "Two storey side extension", 
                "New detached dwelling",
                "Change of use to residential",
                "Conservatory to rear",
                "Loft conversion with dormer",
                "New commercial unit"
            ]),
            "ward": random.choice(wards),
            "case_officer": random.choice(officers),
            "date_received": app_date.strftime("%Y-%m-%d"),
            "target_decision_date": target_date.strftime("%Y-%m-%d"),
            "consultation_end": (app_date + timedelta(weeks=3)).strftime("%Y-%m-%d") if random.choice([True, False]) else None,
            "public_comments": random.randint(0, 15),
            "site_visit_required": random.choice([True, False]),
            "committee_required": random.choice([True, False]),
            "listed_building_affected": random.choice([True, False, False, False]),  # Less common
            "conservation_area": random.choice([True, False, False])
        }
        applications.append(application)
    
    return {"applications": applications, "total": len(applications)}

@regulatory_app.get("/api/planning/applications/{application_id}")
async def get_planning_application(application_id: str):
    """Get detailed planning application"""
    return {
        "id": application_id,
        "application_type": "Householder",
        "status": "Under Assessment",
        "site_address": "123 Main Street, Central Ward",
        "applicant_name": "John Smith",
        "agent_name": "Planning Associates Ltd",
        "description": "Single storey rear extension",
        "case_officer": "Sarah Johnson",
        "date_received": "2025-08-15",
        "target_decision_date": "2025-10-10",
        "consultation_responses": [
            {"consultee": "Highways", "response": "No objection", "date": "2025-08-25"},
            {"consultee": "Environmental Health", "response": "No concerns", "date": "2025-08-28"},
            {"consultee": "Parish Council", "response": "Support", "date": "2025-08-30"}
        ],
        "documents": [
            {"name": "Site Plan", "type": "Drawing", "uploaded": "2025-08-15"},
            {"name": "Design Statement", "type": "Supporting Document", "uploaded": "2025-08-15"}
        ],
        "site_visit_date": "2025-09-05",
        "recommendation": "Approve with conditions"
    }

# ============================================================================
# BUILDING CONTROL API
# ============================================================================

@regulatory_app.get("/api/building-control/applications")
async def get_building_control_applications(
    stage: Optional[BuildingControlStage] = None,
    officer: Optional[str] = None,
    limit: int = Query(30, le=100)
):
    """Get building control applications"""
    applications = []
    stages = list(BuildingControlStage) if not stage else [stage]
    officers = ["John Smith", "Anna Taylor", "Robert Green", "Helen White"] if not officer else [officer]
    
    for i in range(min(limit, 20)):
        app_date = datetime.now() - timedelta(days=random.randint(1, 120))
        
        application = {
            "id": f"BC/24/{random.randint(100, 999):03d}",
            "application_type": random.choice(list(BuildingControlType)).value,
            "stage": random.choice(stages).value,
            "site_address": f"{random.randint(1, 999)} {random.choice(['Oak Avenue', 'Elm Close', 'Birch Road', 'Cedar Drive'])}",
            "applicant_name": f"{random.choice(['Alice', 'Bob', 'Charlie', 'Diana'])} {random.choice(['Wilson', 'Davis', 'Miller', 'Moore'])}",
            "description": random.choice([
                "New build dwelling",
                "Single storey extension",
                "Loft conversion",
                "Garage construction",
                "Commercial fit-out"
            ]),
            "inspecting_officer": random.choice(officers),
            "date_received": app_date.strftime("%Y-%m-%d"),
            "next_inspection": (datetime.now() + timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d"),
            "fees_paid": random.choice([True, False]),
            "estimated_cost": random.randint(15000, 250000)
        }
        applications.append(application)
    
    return {"applications": applications, "total": len(applications)}

@regulatory_app.post("/api/building-control/inspections/{application_id}")
async def book_inspection(
    application_id: str,
    inspection_type: str,
    preferred_date: str
):
    """Book building control inspection"""
    return {
        "success": True,
        "inspection_id": f"INS/{random.randint(10000, 99999)}",
        "application_id": application_id,
        "inspection_type": inspection_type,
        "scheduled_date": preferred_date,
        "inspector": "John Smith",
        "time_slot": "09:00-12:00",
        "message": "Inspection booked successfully"
    }

# ============================================================================
# LAND CHARGES API  
# ============================================================================

@regulatory_app.get("/api/land-charges/searches")
async def get_land_charges_searches(
    search_type: Optional[LandChargesSearchType] = None,
    status: Optional[LandChargesStatus] = None,
    urgent_only: bool = False,
    limit: int = Query(50, le=200)
):
    """Get land charges searches"""
    searches = []
    types = list(LandChargesSearchType) if not search_type else [search_type]
    statuses = list(LandChargesStatus) if not status else [status]
    
    for i in range(min(limit, 30)):
        search_date = datetime.now() - timedelta(days=random.randint(0, 60))
        is_urgent = random.choice([True, False]) if not urgent_only else True
        
        search = {
            "id": f"LLC/{random.randint(10000, 99999)}",
            "search_type": random.choice(types).value,
            "status": random.choice(statuses).value,
            "property_address": f"{random.randint(1, 999)} {random.choice(['Manor Road', 'Station Road', 'The Green', 'Market Square'])}",
            "applicant_name": f"{random.choice(['Smith & Partners', 'Jones Solicitors', 'Brown & Co', 'Wilson Legal'])}",
            "date_received": search_date.strftime("%Y-%m-%d"),
            "processing_officer": random.choice(["Lisa Brown", "Mark Taylor", "Sophie Wilson", "James Clark"]),
            "fee_amount": random.choice([100, 120, 150, 200]),
            "fee_paid": random.choice([True, False]),
            "urgent_search": is_urgent,
            "target_completion": (search_date + timedelta(days=3 if is_urgent else 10)).strftime("%Y-%m-%d")
        }
        searches.append(search)
    
    return {"searches": searches, "total": len(searches)}

@regulatory_app.post("/api/land-charges/searches")
async def create_land_charges_search(search_data: dict):
    """Create new land charges search"""
    search_id = f"LLC/{random.randint(10000, 99999)}"
    return {
        "success": True,
        "search_id": search_id,
        "reference": search_id,
        "estimated_completion": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
        "fee_amount": 120.00,
        "payment_reference": f"PAY{random.randint(100000, 999999)}"
    }

# ============================================================================
# WASTE REGULATORY SERVICES API (NEW)
# ============================================================================

@regulatory_app.get("/api/waste-regulatory/cases")
async def get_waste_regulatory_cases(
    licence_type: Optional[WasteLicenceType] = None,
    status: Optional[WasteComplianceStatus] = None,
    inspection_due: bool = False,
    limit: int = Query(30, le=100)
):
    """Get waste regulatory cases"""
    cases = []
    types = list(WasteLicenceType) if not licence_type else [licence_type]
    statuses = list(WasteComplianceStatus) if not status else [status]
    
    for i in range(min(limit, 20)):
        issue_date = datetime.now() - timedelta(days=random.randint(30, 1095))  # 1-3 years ago
        
        case = {
            "id": f"WR/{random.randint(1000, 9999)}",
            "licence_type": random.choice(types).value,
            "status": random.choice(statuses).value,
            "business_name": f"{random.choice(['Green', 'Eco', 'Clean', 'Safe', 'Premier'])} {random.choice(['Waste', 'Recycling', 'Environmental', 'Skip', 'Disposal'])} {random.choice(['Ltd', 'Services', 'Solutions', 'Group'])}",
            "business_address": f"{random.randint(1, 999)} {random.choice(['Industrial Estate', 'Business Park', 'Trading Estate', 'Commercial Road'])}",
            "license_holder": f"{random.choice(['John', 'Sarah', 'Mike', 'Emma'])} {random.choice(['Thompson', 'Edwards', 'Roberts', 'Phillips'])}",
            "licence_number": f"WCL/{random.randint(100000, 999999)}",
            "issue_date": issue_date.strftime("%Y-%m-%d"),
            "expiry_date": (issue_date + timedelta(days=1095)).strftime("%Y-%m-%d"),  # 3 years
            "last_inspection": (datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d"),
            "next_inspection": (datetime.now() + timedelta(days=random.randint(30, 180))).strftime("%Y-%m-%d"),
            "inspecting_officer": random.choice(["Tom Wilson", "Kate Johnson", "Paul Davis", "Amy Brown"]),
            "annual_fee_due": random.choice([154.00, 308.00, 462.00]),  # Standard EA fees
            "compliance_score": random.randint(70, 100)
        }
        cases.append(case)
    
    return {"cases": cases, "total": len(cases)}

@regulatory_app.post("/api/waste-regulatory/inspections/{case_id}")
async def schedule_waste_inspection(case_id: str, inspection_data: dict):
    """Schedule waste regulatory inspection"""
    return {
        "success": True,
        "inspection_id": f"WI/{random.randint(10000, 99999)}",
        "case_id": case_id,
        "scheduled_date": inspection_data.get("date"),
        "inspector": inspection_data.get("officer", "Tom Wilson"),
        "inspection_type": inspection_data.get("type", "Routine Compliance"),
        "checklist_items": [
            "Waste carrier licence displayed",
            "Duty of care documentation",
            "Waste storage compliance",
            "Environmental permit compliance",
            "Health & safety procedures"
        ]
    }

# ============================================================================
# PRIVATE SECTOR HOUSING API (NEW)
# ============================================================================

@regulatory_app.get("/api/housing/cases")
async def get_housing_cases(
    enforcement_type: Optional[HousingEnforcementType] = None,
    status: Optional[HousingComplianceStatus] = None,
    inspection_due: bool = False,
    limit: int = Query(30, le=100)
):
    """Get private sector housing cases"""
    cases = []
    types = list(HousingEnforcementType) if not enforcement_type else [enforcement_type]
    statuses = list(HousingComplianceStatus) if not status else [status]
    
    for i in range(min(limit, 25)):
        report_date = datetime.now() - timedelta(days=random.randint(1, 365))
        
        case = {
            "id": f"HSG/{random.randint(1000, 9999)}",
            "enforcement_type": random.choice(types).value,
            "status": random.choice(statuses).value,
            "property_address": f"Flat {random.randint(1, 20)}, {random.randint(1, 999)} {random.choice(['Victoria Street', 'Queen Road', 'King Avenue', 'Prince Close'])}",
            "property_type": random.choice(["House", "Flat", "HMO", "Studio", "Bedsit"]),
            "landlord_name": f"{random.choice(['Property', 'Housing', 'Estate', 'Rental'])} {random.choice(['Investments', 'Management', 'Solutions', 'Group'])} Ltd",
            "tenant_contact": f"Tenant {random.randint(1, 100)}",
            "date_reported": report_date.strftime("%Y-%m-%d"),
            "inspection_date": (report_date + timedelta(days=random.randint(5, 30))).strftime("%Y-%m-%d"),
            "inspecting_officer": random.choice(["Rachel Green", "Mark Thompson", "Lucy Wilson", "Steve Clark"]),
            "hhsrs_score": random.randint(200, 1500) if random.choice([True, False]) else None,
            "licence_required": random.choice([True, False]),
            "licence_number": f"HMO/{random.randint(1000, 9999)}" if random.choice([True, False]) else None,
            "priority_score": random.randint(1, 10)
        }
        cases.append(case)
    
    return {"cases": cases, "total": len(cases)}

@regulatory_app.post("/api/housing/inspections/{case_id}")
async def schedule_housing_inspection(case_id: str, inspection_data: dict):
    """Schedule housing standards inspection"""
    return {
        "success": True,
        "inspection_id": f"HI/{random.randint(10000, 99999)}",
        "case_id": case_id,
        "scheduled_date": inspection_data.get("date"),
        "inspector": inspection_data.get("officer", "Rachel Green"),
        "inspection_type": "HHSRS Assessment",
        "assessment_areas": [
            "Dampness and mould",
            "Excess cold/heat",
            "Electrical hazards", 
            "Fire safety",
            "Structural stability",
            "Space and overcrowding",
            "Water supply",
            "Drainage and sanitation"
        ]
    }

# ============================================================================
# INTEGRATED DASHBOARD API
# ============================================================================

@regulatory_app.get("/api/dashboard/overview")
async def get_integrated_dashboard():
    """Get comprehensive regulatory dashboard overview"""
    return {
        "summary_stats": {
            "total_active_cases": random.randint(800, 1200),
            "cases_this_month": random.randint(150, 250),
            "urgent_cases": random.randint(25, 45),
            "overdue_cases": random.randint(15, 35)
        },
        "by_service": {
            "planning": {
                "active": random.randint(200, 350),
                "pending_decision": random.randint(80, 120),
                "avg_processing_time": f"{random.randint(8, 12)} weeks"
            },
            "building_control": {
                "active": random.randint(150, 250),
                "inspections_due": random.randint(25, 45),
                "certificates_issued_month": random.randint(35, 65)
            },
            "land_charges": {
                "active": random.randint(180, 280),
                "urgent_searches": random.randint(12, 25),
                "avg_processing_time": f"{random.randint(5, 8)} days"
            },
            "waste_regulatory": {
                "active_licences": random.randint(450, 650),
                "inspections_due": random.randint(30, 50),
                "compliance_rate": f"{random.randint(85, 95)}%"
            },
            "housing": {
                "active_cases": random.randint(120, 200),
                "inspections_due": random.randint(20, 40),
                "enforcement_actions": random.randint(15, 30)
            }
        },
        "performance_indicators": {
            "planning_in_time": f"{random.randint(75, 90)}%",
            "building_control_satisfaction": f"{random.randint(88, 96)}%",
            "land_charges_sla": f"{random.randint(92, 98)}%",
            "waste_compliance": f"{random.randint(82, 94)}%", 
            "housing_response_time": f"{random.randint(3, 7)} days"
        },
        "recent_activity": [
            {"type": "Planning", "action": "Application approved", "ref": f"24/{random.randint(1000, 9999)}", "time": "2 hours ago"},
            {"type": "Building Control", "action": "Inspection completed", "ref": f"BC/24/{random.randint(100, 999)}", "time": "4 hours ago"},
            {"type": "Housing", "action": "Improvement notice served", "ref": f"HSG/{random.randint(1000, 9999)}", "time": "6 hours ago"},
            {"type": "Waste", "action": "Licence renewed", "ref": f"WR/{random.randint(1000, 9999)}", "time": "1 day ago"}
        ]
    }

# ============================================================================
# USER MANAGEMENT API
# ============================================================================

@regulatory_app.get("/api/users/permissions/{user_id}")
async def get_user_permissions(user_id: str):
    """Get user permissions and access rights"""
    return {
        "user_id": user_id,
        "role": "Case Officer",
        "department": "Planning & Transportation",
        "permissions": {
            "can_view": ["PLANNING", "BUILDING_CONTROL"],
            "can_edit": ["PLANNING"],
            "can_approve": [],
            "can_assign": False,
            "geographical_access": ["Central Ward", "North Ward"]
        },
        "case_load": {
            "assigned_cases": random.randint(15, 35),
            "overdue_cases": random.randint(2, 8),
            "this_week_targets": random.randint(8, 15)
        }
    }

# ============================================================================
# AUDIT TRAIL API
# ============================================================================

@regulatory_app.get("/api/audit/case/{case_id}")
async def get_case_audit_trail(case_id: str):
    """Get complete audit trail for a case"""
    entries = []
    for i in range(random.randint(10, 25)):
        entry_date = datetime.now() - timedelta(days=random.randint(0, 90))
        entries.append({
            "timestamp": entry_date.isoformat(),
            "action": random.choice(list(AuditAction)).value,
            "user": f"{random.choice(['Sarah', 'Mike', 'Emma', 'David'])} {random.choice(['Johnson', 'Peters', 'Wilson', 'Clark'])}",
            "details": "Case status updated",
            "ip_address": f"192.168.1.{random.randint(1, 254)}",
            "foi_exempt": random.choice([True, False])
        })
    
    return {
        "case_id": case_id,
        "audit_entries": sorted(entries, key=lambda x: x["timestamp"], reverse=True),
        "total_entries": len(entries)
    }

# ============================================================================
# REPORTING API
# ============================================================================

@regulatory_app.get("/api/reports/performance")
async def get_performance_report(
    service: Optional[str] = None,
    period: str = Query("month", regex="^(week|month|quarter|year)$"),
    format: str = Query("json", regex="^(json|csv|pdf)$")
):
    """Generate performance reports"""
    
    if service == "planning":
        data = {
            "service": "Planning Applications",
            "period": period,
            "metrics": {
                "applications_received": random.randint(50, 150),
                "applications_determined": random.randint(45, 140),
                "average_determination_time": f"{random.randint(8, 12)} weeks",
                "in_time_performance": f"{random.randint(75, 90)}%",
                "appeals_received": random.randint(2, 8),
                "appeals_allowed": random.randint(0, 3)
            }
        }
    else:
        data = {
            "service": "All Regulatory Services",
            "period": period,
            "summary": {
                "total_cases": random.randint(300, 800),
                "cases_closed": random.randint(280, 750),
                "customer_satisfaction": f"{random.randint(85, 95)}%",
                "revenue_generated": f"£{random.randint(50, 150)}k"
            }
        }
    
    return data

# Initialize the regulatory platform
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(regulatory_app, host="0.0.0.0", port=8001)