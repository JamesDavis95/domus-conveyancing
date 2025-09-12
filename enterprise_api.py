# 🏛️ **ENTERPRISE API SYSTEM**
# Complete backend for multi-tenant council platform

from fastapi import APIRouter, HTTPException, Depends, Request, Form, UploadFile, File as FastAPIFile, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
import uuid
from enum import Enum

# Import our enterprise models
from enterprise_models import *

router = APIRouter(prefix="/api", tags=["enterprise"])

# ==================== AUTHENTICATION & AUTHORIZATION ====================

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    # In a real implementation, validate JWT token
    # For now, return mock user for demo
    return {
        "id": 1,
        "email": "admin@eastherts.gov.uk",
        "name": "Admin User",
        "role": "council_admin",
        "organization_id": 1,
        "organization_name": "East Hertfordshire District Council"
    }

# ==================== DASHBOARD APIs ====================

@router.get("/dashboard/overview")
async def get_dashboard_overview(user: dict = Depends(get_current_user)):
    """Get main dashboard overview"""
    return {
        "organization": {
            "name": user["organization_name"],
            "type": "District Council",
            "subscription_tier": "Enterprise"
        },
        "key_metrics": {
            "active_matters": {
                "value": 47,
                "change": "+12%",
                "trend": "up",
                "period": "this month"
            },
            "pending_reviews": {
                "value": 23,
                "change": "-5%", 
                "trend": "down",
                "period": "this week"
            },
            "monthly_revenue": {
                "value": 28450.00,
                "change": "+18%",
                "trend": "up",
                "period": "vs last month"
            },
            "avg_processing_time": {
                "value": 2.3,
                "unit": "hours",
                "change": "40% faster",
                "trend": "up"
            }
        },
        "system_status": {
            "api_gateway": "online",
            "document_processing": "operational", 
            "council_integrations": "47 connected",
            "ai_processing": "ready"
        },
        "recent_matters": [
            {
                "id": "DOM-2025-001",
                "property_address": "123 High Street, Hertford",
                "council": "East Hertfordshire DC",
                "status": "in_progress",
                "assigned_to": "Sarah Johnson",
                "due_date": "2025-09-15",
                "priority": "high"
            },
            {
                "id": "DOM-2025-002", 
                "property_address": "45 Mill Lane, Ware",
                "council": "East Hertfordshire DC",
                "status": "pending_review",
                "assigned_to": "Mike Chen",
                "due_date": "2025-09-18",
                "priority": "normal"
            },
            {
                "id": "DOM-2025-003",
                "property_address": "78 Castle Street, Hertford", 
                "council": "East Hertfordshire DC",
                "status": "draft",
                "assigned_to": "Emma Wilson",
                "due_date": "2025-09-20",
                "priority": "normal"
            }
        ]
    }

# ==================== MATTERS MANAGEMENT APIs ====================

@router.get("/matters")
async def get_matters(
    status: Optional[str] = None,
    department: Optional[str] = None, 
    assigned_to: Optional[str] = None,
    search: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get all matters with filtering"""
    
    # Mock data - in real implementation, query database
    matters = [
        {
            "id": "DOM-2025-001",
            "ref": "DOM-2025-001", 
            "title": "Local Search - 123 High Street",
            "property_address": "123 High Street, Hertford, SG14 1AB",
            "postcode": "SG14 1AB",
            "council": "East Hertfordshire DC",
            "department": "planning",
            "status": "in_progress",
            "priority": "high",
            "assigned_to": {
                "id": 2,
                "name": "Sarah Johnson",
                "email": "s.johnson@eastherts.gov.uk"
            },
            "created_date": "2025-09-10T10:30:00Z",
            "due_date": "2025-09-15T17:00:00Z",
            "estimated_cost": 125.00,
            "actual_cost": None,
            "billing_code": "PLAN-2025-Q3"
        },
        {
            "id": "DOM-2025-002",
            "ref": "DOM-2025-002",
            "title": "Environmental Search - 45 Mill Lane", 
            "property_address": "45 Mill Lane, Ware, SG12 9HT",
            "postcode": "SG12 9HT",
            "council": "East Hertfordshire DC",
            "department": "housing",
            "status": "pending_review",
            "priority": "normal",
            "assigned_to": {
                "id": 3,
                "name": "Mike Chen", 
                "email": "m.chen@eastherts.gov.uk"
            },
            "created_date": "2025-09-11T09:15:00Z",
            "due_date": "2025-09-18T17:00:00Z", 
            "estimated_cost": 95.00,
            "actual_cost": None,
            "billing_code": "HOUS-2025-Q3"
        },
        {
            "id": "DOM-2025-003",
            "ref": "DOM-2025-003",
            "title": "Planning Search - 78 Castle Street",
            "property_address": "78 Castle Street, Hertford, SG14 2DH", 
            "postcode": "SG14 2DH",
            "council": "East Hertfordshire DC",
            "department": "legal",
            "status": "draft", 
            "priority": "normal",
            "assigned_to": {
                "id": 4,
                "name": "Emma Wilson",
                "email": "e.wilson@eastherts.gov.uk"
            },
            "created_date": "2025-09-11T14:20:00Z",
            "due_date": "2025-09-20T17:00:00Z",
            "estimated_cost": 150.00,
            "actual_cost": None,
            "billing_code": "LEGAL-2025-Q3"
        }
    ]
    
    # Apply filters
    filtered_matters = matters
    if status:
        filtered_matters = [m for m in filtered_matters if m["status"] == status]
    if department:
        filtered_matters = [m for m in filtered_matters if m["department"] == department]
    if assigned_to:
        filtered_matters = [m for m in filtered_matters if m["assigned_to"]["name"] == assigned_to]
    if search:
        search_lower = search.lower()
        filtered_matters = [m for m in filtered_matters if 
            search_lower in m["ref"].lower() or 
            search_lower in m["property_address"].lower() or
            search_lower in m["postcode"].lower()
        ]
    
    return {
        "matters": filtered_matters,
        "total_count": len(filtered_matters),
        "filters_applied": {
            "status": status,
            "department": department, 
            "assigned_to": assigned_to,
            "search": search
        }
    }

@router.post("/matters")
async def create_matter(
    title: str = Form(...),
    property_address: str = Form(...),
    postcode: str = Form(...),
    department: str = Form(...),
    priority: str = Form("normal"),
    assigned_to_id: Optional[int] = Form(None),
    user: dict = Depends(get_current_user)
):
    """Create new matter"""
    
    # Generate unique reference
    matter_ref = f"DOM-{datetime.now().year}-{str(uuid.uuid4())[:3].upper()}"
    
    new_matter = {
        "id": matter_ref,
        "ref": matter_ref,
        "title": title,
        "property_address": property_address,
        "postcode": postcode,
        "department": department,
        "priority": priority,
        "status": "draft",
        "created_by": user["id"],
        "assigned_to_id": assigned_to_id,
        "created_date": datetime.utcnow().isoformat(),
        "organization_id": user["organization_id"]
    }
    
    # In real implementation, save to database
    
    return {
        "success": True,
        "matter": new_matter,
        "message": f"Matter {matter_ref} created successfully"
    }

@router.get("/matters/{matter_id}")
async def get_matter_details(matter_id: str, user: dict = Depends(get_current_user)):
    """Get detailed matter information"""
    
    # Mock detailed matter data
    matter_details = {
        "id": matter_id,
        "ref": matter_id,
        "title": "Local Search - 123 High Street",
        "description": "Comprehensive local search for property purchase",
        "property_details": {
            "address": "123 High Street, Hertford, SG14 1AB",
            "postcode": "SG14 1AB", 
            "uprn": "100021065123",
            "title_number": "HD123456"
        },
        "status": "in_progress",
        "priority": "high",
        "department": "planning",
        "workflow_steps": [
            {
                "id": 1,
                "name": "Document Upload",
                "status": "completed",
                "completed_at": "2025-09-10T11:00:00Z",
                "assigned_to": "Sarah Johnson"
            },
            {
                "id": 2,
                "name": "AI Processing",
                "status": "completed", 
                "completed_at": "2025-09-10T11:30:00Z",
                "assigned_to": "System"
            },
            {
                "id": 3,
                "name": "Quality Review",
                "status": "in_progress",
                "started_at": "2025-09-11T09:00:00Z",
                "assigned_to": "Sarah Johnson"
            },
            {
                "id": 4,
                "name": "Supervisor Approval", 
                "status": "pending",
                "assigned_to": "Department Head"
            }
        ],
        "files": [
            {
                "id": 1,
                "filename": "local_search_123_high_st.pdf",
                "file_type": "local_search",
                "uploaded_at": "2025-09-10T10:45:00Z",
                "processing_status": "completed",
                "ai_confidence": 0.94
            }
        ],
        "findings": [
            {
                "category": "Planning",
                "key": "Planning Applications",
                "value": "No current applications affecting property",
                "confidence": 0.95
            },
            {
                "category": "Environmental", 
                "key": "Flood Risk",
                "value": "Low risk - Flood Zone 1",
                "confidence": 0.98
            }
        ],
        "risks": [
            {
                "code": "PLAN001",
                "title": "Nearby Development",
                "description": "Large residential development planned 200m from property",
                "level": "medium",
                "mitigation_required": True
            }
        ],
        "financial": {
            "estimated_cost": 125.00,
            "actual_cost": 125.00,
            "billing_code": "PLAN-2025-Q3",
            "invoice_status": "pending"
        }
    }
    
    return matter_details

# ==================== USER MANAGEMENT APIs ====================

@router.get("/users")
async def get_users(user: dict = Depends(get_current_user)):
    """Get all users in organization"""
    
    users = [
        {
            "id": 2,
            "email": "s.johnson@eastherts.gov.uk",
            "first_name": "Sarah",
            "last_name": "Johnson", 
            "full_name": "Sarah Johnson",
            "job_title": "Senior Planning Officer",
            "department": "planning",
            "role": "senior_officer",
            "is_active": True,
            "last_login": "2025-09-11T12:30:00Z",
            "created_at": "2025-01-15T09:00:00Z"
        },
        {
            "id": 3,
            "email": "m.chen@eastherts.gov.uk", 
            "first_name": "Mike",
            "last_name": "Chen",
            "full_name": "Mike Chen",
            "job_title": "Housing Officer",
            "department": "housing",
            "role": "officer", 
            "is_active": True,
            "last_login": "2025-09-10T16:45:00Z",
            "created_at": "2025-02-20T10:30:00Z"
        },
        {
            "id": 4,
            "email": "e.wilson@eastherts.gov.uk",
            "first_name": "Emma", 
            "last_name": "Wilson",
            "full_name": "Emma Wilson",
            "job_title": "Legal Assistant",
            "department": "legal",
            "role": "officer",
            "is_active": True,
            "last_login": "2025-09-11T08:15:00Z", 
            "created_at": "2025-03-10T14:20:00Z"
        }
    ]
    
    return {
        "users": users,
        "total_count": len(users),
        "active_count": len([u for u in users if u["is_active"]])
    }

@router.post("/users")
async def create_user(
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    department: str = Form(...),
    role: str = Form("officer"),
    job_title: Optional[str] = Form(None),
    user: dict = Depends(get_current_user)
):
    """Create new user"""
    
    new_user = {
        "id": len([]) + 10,  # Mock ID generation
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "full_name": f"{first_name} {last_name}",
        "job_title": job_title,
        "department": department,
        "role": role,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "organization_id": user["organization_id"]
    }
    
    return {
        "success": True,
        "user": new_user,
        "message": f"User {email} created successfully"
    }

# ==================== FINANCIAL MANAGEMENT APIs ====================

@router.get("/billing/summary")
async def get_billing_summary(user: dict = Depends(get_current_user)):
    """Get financial summary"""
    
    return {
        "current_month": {
            "revenue": 28450.00,
            "costs": 12800.00,
            "profit": 15650.00,
            "matter_count": 47
        },
        "year_to_date": {
            "revenue": 186250.00,
            "costs": 84300.00,
            "profit": 101950.00,
            "matter_count": 312
        },
        "outstanding": {
            "amount": 4125.00,
            "invoice_count": 3,
            "overdue_amount": 850.00
        },
        "averages": {
            "per_matter": 125.50,
            "processing_cost": 28.75,
            "profit_margin": 0.68
        },
        "recent_invoices": [
            {
                "id": "INV-2025-001",
                "department": "Planning",
                "period": "August 2025",
                "amount": 12450.00,
                "status": "paid",
                "due_date": "2025-08-31",
                "paid_date": "2025-08-28"
            },
            {
                "id": "INV-2025-002", 
                "department": "Housing",
                "period": "August 2025",
                "amount": 8750.00,
                "status": "paid",
                "due_date": "2025-08-31", 
                "paid_date": "2025-08-30"
            },
            {
                "id": "INV-2025-003",
                "department": "Legal",
                "period": "September 2025", 
                "amount": 6200.00,
                "status": "pending",
                "due_date": "2025-09-30",
                "paid_date": None
            }
        ]
    }

@router.get("/billing/invoices")
async def get_invoices(
    status: Optional[str] = None,
    department: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get invoices with filtering"""
    
    invoices = [
        {
            "id": "INV-2025-001",
            "invoice_number": "INV-2025-001",
            "department": "Planning", 
            "period_start": "2025-08-01",
            "period_end": "2025-08-31",
            "subtotal": 10375.00,
            "vat_amount": 2075.00,
            "total_amount": 12450.00,
            "status": "paid",
            "issued_date": "2025-09-01",
            "due_date": "2025-08-31",
            "paid_date": "2025-08-28",
            "line_item_count": 23
        }
    ]
    
    return {
        "invoices": invoices,
        "total_count": len(invoices)
    }

# ==================== DOCUMENT PROCESSING APIs ====================

@router.post("/documents/upload")
async def upload_document(
    files: List[UploadFile],
    matter_id: str = Form(...),
    document_type: str = Form(...),
    user: dict = Depends(get_current_user)
):
    """Upload and process documents"""
    
    processed_files = []
    
    for file in files:
        # In real implementation, save file and process with AI
        file_id = str(uuid.uuid4())
        
        processed_file = {
            "id": file_id,
            "filename": file.filename,
            "original_filename": file.filename,
            "file_size": file.size if hasattr(file, 'size') else None,
            "file_type": document_type,
            "processing_status": "queued",
            "uploaded_at": datetime.utcnow().isoformat(),
            "matter_id": matter_id
        }
        
        processed_files.append(processed_file)
    
    return {
        "success": True,
        "files": processed_files,
        "message": f"Uploaded {len(files)} files for processing"
    }

@router.get("/documents/processing-queue")
async def get_processing_queue(user: dict = Depends(get_current_user)):
    """Get document processing status"""
    
    queue = [
        {
            "id": 1,
            "filename": "search_123_high_st.pdf",
            "matter_id": "DOM-2025-001",
            "document_type": "local_search",
            "status": "processing",
            "progress": 85,
            "ai_confidence": 92,
            "started_at": "2025-09-11T10:30:00Z",
            "estimated_completion": "2025-09-11T11:00:00Z"
        },
        {
            "id": 2,
            "filename": "planning_docs_45_mill.pdf", 
            "matter_id": "DOM-2025-002",
            "document_type": "planning_documents",
            "status": "completed",
            "progress": 100,
            "ai_confidence": 88,
            "started_at": "2025-09-11T09:15:00Z",
            "completed_at": "2025-09-11T09:45:00Z"
        }
    ]
    
    return {
        "queue": queue,
        "total_count": len(queue),
        "processing_count": len([q for q in queue if q["status"] == "processing"]),
        "completed_count": len([q for q in queue if q["status"] == "completed"])
    }

# ==================== SYSTEM INTEGRATIONS APIs ====================

@router.get("/integrations")  
async def get_integrations(user: dict = Depends(get_current_user)):
    """Get system integration status"""
    
    integrations = [
        {
            "id": 1,
            "name": "Capita Academy",
            "integration_type": "crm",
            "provider": "Capita",
            "is_active": True,
            "last_sync": "2025-09-11T10:45:00Z",
            "sync_status": "success",
            "config": {
                "endpoint": "https://academy.capita.com/api/v2",
                "sync_frequency": "hourly"
            }
        },
        {
            "id": 2,
            "name": "Civica CX", 
            "integration_type": "finance",
            "provider": "Civica",
            "is_active": True,
            "last_sync": "2025-09-11T11:00:00Z",
            "sync_status": "success",
            "config": {
                "endpoint": "https://cx.civica.com/api/v3",
                "sync_frequency": "daily"
            }
        },
        {
            "id": 3,
            "name": "SharePoint",
            "integration_type": "document_store", 
            "provider": "Microsoft",
            "is_active": False,
            "last_sync": None,
            "sync_status": "pending_setup",
            "config": {
                "site_url": "https://eastherts.sharepoint.com",
                "document_library": "ConveyancingDocs"
            }
        }
    ]
    
    return {
        "integrations": integrations,
        "total_count": len(integrations),
        "active_count": len([i for i in integrations if i["is_active"]]),
        "connected_systems": [i["name"] for i in integrations if i["is_active"]]
    }

# ==================== COMPLIANCE & AUDIT APIs ====================

@router.get("/compliance/status")
async def get_compliance_status(user: dict = Depends(get_current_user)):
    """Get compliance and security status"""
    
    return {
        "compliance_standards": {
            "gdpr": {
                "status": "compliant",
                "last_audit": "2025-06-15",
                "next_review": "2025-12-15",
                "certificate_url": "/certificates/gdpr-2025.pdf"
            },
            "iso_27001": {
                "status": "certified", 
                "last_audit": "2025-05-20",
                "next_review": "2026-05-20",
                "certificate_url": "/certificates/iso27001-2025.pdf"
            },
            "cyber_essentials_plus": {
                "status": "certified",
                "last_audit": "2025-07-10", 
                "next_review": "2026-07-10",
                "certificate_url": "/certificates/cyber-essentials-plus-2025.pdf"
            }
        },
        "data_protection": {
            "retention_policy": "automated",
            "backup_status": "active", 
            "encryption": "aes_256",
            "data_location": "uk_only"
        },
        "audit_trail": {
            "logging_active": True,
            "retention_period": "7_years",
            "log_entries_today": 1247,
            "integrity_check": "passed"
        },
        "sla_compliance": {
            "uptime": 99.87,
            "target_uptime": 99.9,
            "avg_response_time": "1.2s",
            "target_response_time": "2.0s"
        }
    }

# ==================== CALENDAR & TASK MANAGEMENT APIs ====================

@router.get("/calendar/events")
async def get_calendar_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_id: Optional[int] = None,
    user: dict = Depends(get_current_user)
):
    """Get calendar events and appointments"""
    
    events = [
        {
            "id": 1,
            "title": "Matter Review: DOM-2025-001",
            "description": "Quality review of local search documents",
            "start_datetime": "2025-09-12T10:00:00Z",
            "end_datetime": "2025-09-12T11:00:00Z",
            "event_type": "matter_review",
            "matter_id": "DOM-2025-001",
            "assigned_to": {
                "id": 2,
                "name": "Sarah Johnson"
            },
            "status": "scheduled",
            "priority": "high",
            "location": "Planning Department"
        },
        {
            "id": 2,
            "title": "Client Meeting: Environmental Report",
            "description": "Discuss environmental findings with client",
            "start_datetime": "2025-09-12T14:30:00Z",
            "end_datetime": "2025-09-12T15:30:00Z",
            "event_type": "client_meeting",
            "matter_id": "DOM-2025-002",
            "assigned_to": {
                "id": 3,
                "name": "Mike Chen"
            },
            "status": "confirmed",
            "priority": "medium",
            "location": "Meeting Room B"
        },
        {
            "id": 3,
            "title": "Document Processing Review",
            "description": "Weekly review of AI processing accuracy",
            "start_datetime": "2025-09-13T09:00:00Z",
            "end_datetime": "2025-09-13T10:00:00Z",
            "event_type": "team_meeting",
            "matter_id": None,
            "assigned_to": {
                "id": 4,
                "name": "Emma Wilson"
            },
            "status": "scheduled",
            "priority": "normal",
            "location": "Conference Room"
        }
    ]
    
    return {
        "events": events,
        "total_count": len(events),
        "date_range": {
            "start": start_date or "2025-09-01",
            "end": end_date or "2025-09-30"
        }
    }

@router.post("/calendar/events")
async def create_calendar_event(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    start_datetime: str = Form(...),
    end_datetime: str = Form(...),
    event_type: str = Form("general"),
    matter_id: Optional[str] = Form(None),
    assigned_to_id: Optional[int] = Form(None),
    priority: str = Form("normal"),
    location: Optional[str] = Form(None),
    user: dict = Depends(get_current_user)
):
    """Create new calendar event"""
    
    event_id = len([]) + 100  # Mock ID generation
    
    new_event = {
        "id": event_id,
        "title": title,
        "description": description,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "event_type": event_type,
        "matter_id": matter_id,
        "assigned_to_id": assigned_to_id or user["id"],
        "priority": priority,
        "location": location,
        "status": "scheduled",
        "created_by": user["id"],
        "created_at": datetime.utcnow().isoformat(),
        "organization_id": user["organization_id"]
    }
    
    return {
        "success": True,
        "event": new_event,
        "message": f"Calendar event '{title}' created successfully"
    }

@router.get("/tasks")
async def get_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[int] = None,
    matter_id: Optional[str] = None,
    due_date: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get tasks with filtering"""
    
    tasks = [
        {
            "id": 1,
            "title": "Review Local Search Documents",
            "description": "Quality check of AI-processed local search for DOM-2025-001",
            "task_type": "document_review",
            "matter_id": "DOM-2025-001",
            "status": "in_progress",
            "priority": "high",
            "assigned_to": {
                "id": 2,
                "name": "Sarah Johnson",
                "department": "planning"
            },
            "created_date": "2025-09-11T09:00:00Z",
            "due_date": "2025-09-12T17:00:00Z",
            "estimated_duration": 60,  # minutes
            "actual_duration": None,
            "progress_percentage": 75,
            "tags": ["urgent", "quality-check", "local-search"]
        },
        {
            "id": 2,
            "title": "Client Communication - Environmental Report",
            "description": "Send environmental search results to client with recommendations",
            "task_type": "client_communication",
            "matter_id": "DOM-2025-002",
            "status": "pending",
            "priority": "medium",
            "assigned_to": {
                "id": 3,
                "name": "Mike Chen",
                "department": "housing"
            },
            "created_date": "2025-09-11T14:30:00Z",
            "due_date": "2025-09-13T12:00:00Z",
            "estimated_duration": 30,
            "actual_duration": None,
            "progress_percentage": 0,
            "tags": ["client", "environmental", "report"]
        },
        {
            "id": 3,
            "title": "Process Planning Documents",
            "description": "Upload and process planning documents through AI system",
            "task_type": "document_processing",
            "matter_id": "DOM-2025-003",
            "status": "completed",
            "priority": "normal",
            "assigned_to": {
                "id": 4,
                "name": "Emma Wilson",
                "department": "legal"
            },
            "created_date": "2025-09-10T11:00:00Z",
            "due_date": "2025-09-11T17:00:00Z",
            "estimated_duration": 45,
            "actual_duration": 38,
            "progress_percentage": 100,
            "completed_date": "2025-09-11T16:22:00Z",
            "tags": ["planning", "ai-processing", "completed"]
        }
    ]
    
    # Apply filters
    filtered_tasks = tasks
    if status:
        filtered_tasks = [t for t in filtered_tasks if t["status"] == status]
    if priority:
        filtered_tasks = [t for t in filtered_tasks if t["priority"] == priority]
    if assigned_to:
        filtered_tasks = [t for t in filtered_tasks if t["assigned_to"]["id"] == assigned_to]
    if matter_id:
        filtered_tasks = [t for t in filtered_tasks if t["matter_id"] == matter_id]
    
    return {
        "tasks": filtered_tasks,
        "total_count": len(filtered_tasks),
        "status_summary": {
            "pending": len([t for t in tasks if t["status"] == "pending"]),
            "in_progress": len([t for t in tasks if t["status"] == "in_progress"]),
            "completed": len([t for t in tasks if t["status"] == "completed"]),
            "overdue": len([t for t in tasks if t["status"] == "overdue"])
        }
    }

@router.post("/tasks")
async def create_task(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    task_type: str = Form("general"),
    matter_id: Optional[str] = Form(None),
    priority: str = Form("normal"),
    assigned_to_id: Optional[int] = Form(None),
    due_date: Optional[str] = Form(None),
    estimated_duration: Optional[int] = Form(None),
    tags: Optional[str] = Form(None),
    user: dict = Depends(get_current_user)
):
    """Create new task"""
    
    task_id = len([]) + 200  # Mock ID generation
    
    new_task = {
        "id": task_id,
        "title": title,
        "description": description,
        "task_type": task_type,
        "matter_id": matter_id,
        "status": "pending",
        "priority": priority,
        "assigned_to_id": assigned_to_id or user["id"],
        "due_date": due_date,
        "estimated_duration": estimated_duration,
        "progress_percentage": 0,
        "tags": tags.split(",") if tags else [],
        "created_by": user["id"],
        "created_date": datetime.utcnow().isoformat(),
        "organization_id": user["organization_id"]
    }
    
    return {
        "success": True,
        "task": new_task,
        "message": f"Task '{title}' created successfully"
    }

@router.put("/tasks/{task_id}")
async def update_task(
    task_id: int,
    status: Optional[str] = Form(None),
    progress_percentage: Optional[int] = Form(None),
    actual_duration: Optional[int] = Form(None),
    notes: Optional[str] = Form(None),
    user: dict = Depends(get_current_user)
):
    """Update task status and progress"""
    
    updates = {}
    if status:
        updates["status"] = status
        if status == "completed":
            updates["completed_date"] = datetime.utcnow().isoformat()
            updates["progress_percentage"] = 100
    
    if progress_percentage is not None:
        updates["progress_percentage"] = progress_percentage
    
    if actual_duration:
        updates["actual_duration"] = actual_duration
    
    if notes:
        updates["notes"] = notes
    
    updates["last_modified"] = datetime.utcnow().isoformat()
    updates["modified_by"] = user["id"]
    
    return {
        "success": True,
        "task_id": task_id,
        "updates": updates,
        "message": f"Task {task_id} updated successfully"
    }

@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: int,
    user: dict = Depends(get_current_user)
):
    """Mark a task as completed"""
    
    return {
        "success": True,
        "task_id": task_id,
        "status": "completed",
        "completed_at": datetime.utcnow().isoformat(),
        "completed_by": user["name"],
        "message": f"Task {task_id} marked as completed"
    }

@router.get("/tasks/deadlines")
async def get_task_deadlines(
    days_ahead: int = 7,
    user: dict = Depends(get_current_user)
):
    """Get upcoming task deadlines and reminders"""
    
    upcoming_deadlines = [
        {
            "task_id": 1,
            "title": "Review Local Search Documents",
            "matter_id": "DOM-2025-001",
            "due_date": "2025-09-12T17:00:00Z",
            "hours_remaining": 6,
            "priority": "high",
            "assigned_to": "Sarah Johnson",
            "status": "in_progress",
            "urgency_level": "urgent"
        },
        {
            "task_id": 2,
            "title": "Client Communication - Environmental Report", 
            "matter_id": "DOM-2025-002",
            "due_date": "2025-09-13T12:00:00Z",
            "hours_remaining": 25,
            "priority": "medium",
            "assigned_to": "Mike Chen",
            "status": "pending",
            "urgency_level": "moderate"
        }
    ]
    
    return {
        "upcoming_deadlines": upcoming_deadlines,
        "total_count": len(upcoming_deadlines),
        "urgent_count": len([d for d in upcoming_deadlines if d["urgency_level"] == "urgent"]),
        "reminder_settings": {
            "email_notifications": True,
            "sms_notifications": False,
            "advance_notice_hours": [24, 4, 1]
        }
    }

@router.get("/calendar/team")
async def get_team_calendar(
    department: Optional[str] = None,
    week_of: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get team calendar view with workload distribution"""
    
    team_schedule = [
        {
            "user_id": 2,
            "user_name": "Sarah Johnson",
            "department": "planning",
            "weekly_capacity": 40,  # hours
            "allocated_hours": 32,
            "available_hours": 8,
            "utilization_percentage": 80,
            "tasks": [
                {
                    "id": 1,
                    "title": "Review Local Search Documents",
                    "start_time": "2025-09-12T09:00:00Z",
                    "duration": 120,
                    "matter_id": "DOM-2025-001"
                }
            ],
            "meetings": [
                {
                    "id": 1,
                    "title": "Weekly Planning Review",
                    "start_time": "2025-09-13T14:00:00Z",
                    "duration": 60
                }
            ]
        },
        {
            "user_id": 3,
            "user_name": "Mike Chen",
            "department": "housing",
            "weekly_capacity": 40,
            "allocated_hours": 28,
            "available_hours": 12,
            "utilization_percentage": 70,
            "tasks": [
                {
                    "id": 2,
                    "title": "Environmental Report Analysis",
                    "start_time": "2025-09-12T11:00:00Z",
                    "duration": 180,
                    "matter_id": "DOM-2025-002"
                }
            ],
            "meetings": []
        }
    ]
    
    return {
        "team_schedule": team_schedule,
        "week_summary": {
            "total_team_capacity": 80,
            "total_allocated": 60,
            "total_available": 20,
            "average_utilization": 75
        },
        "workload_alerts": [
            {
                "user_id": 2,
                "user_name": "Sarah Johnson",
                "alert_type": "high_utilization",
                "message": "At 80% capacity - consider redistributing tasks"
            }
        ]
    }

@router.get("/tasks/analytics")
async def get_task_analytics(
    period: str = "month",
    department: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get task performance analytics and insights"""
    
    analytics = {
        "completion_rates": {
            "this_month": 94,
            "last_month": 91,
            "trend": "improving"
        },
        "average_completion_time": {
            "hours": 2.3,
            "vs_estimate": -0.7,  # 0.7 hours faster than estimated
            "trend": "improving"
        },
        "task_types": {
            "document_review": {
                "count": 45,
                "avg_duration": 75,  # minutes
                "completion_rate": 98
            },
            "client_communication": {
                "count": 23,
                "avg_duration": 35,
                "completion_rate": 87
            },
            "document_processing": {
                "count": 67,
                "avg_duration": 42,
                "completion_rate": 95
            }
        },
        "team_performance": {
            "top_performers": [
                {
                    "user_id": 2,
                    "name": "Sarah Johnson",
                    "completion_rate": 97,
                    "avg_quality_score": 4.8
                },
                {
                    "user_id": 4,
                    "name": "Emma Wilson", 
                    "completion_rate": 94,
                    "avg_quality_score": 4.6
                }
            ]
        },
        "bottlenecks": [
            {
                "task_type": "client_communication",
                "avg_delay": 0.5,  # days
                "frequency": 13  # % of tasks
            }
        ]
    }
    
    return analytics

# ==================== SETTINGS APIs ====================

@router.get("/settings")
async def get_system_settings(user: dict = Depends(get_current_user)):
    """Get system configuration"""
    
    return {
        "organization": {
            "name": user["organization_name"],
            "type": "District Council",
            "address": "The Causeway, Bishop's Stortford, Hertfordshire CM23 2ER",
            "phone": "01279 655261",
            "email": "info@eastherts.gov.uk"
        },
        "platform": {
            "version": "2.1.4",
            "environment": "production",
            "default_currency": "GBP",
            "timezone": "Europe/London",
            "date_format": "DD/MM/YYYY"
        },
        "features": {
            "ai_processing": True,
            "multi_user": True,
            "integrations": True,
            "advanced_reporting": True,
            "api_access": True
        },
        "limits": {
            "max_users": 50,
            "max_matters_per_month": 500,
            "storage_limit_gb": 1000,
            "api_calls_per_day": 10000
        }
    }

# ==================== REAL-TIME NOTIFICATIONS SYSTEM ====================

# WebSocket connections for real-time notifications
websocket_connections = []

async def notify_clients(event_type: str, data: dict):
    """Send real-time notifications to all connected clients"""
    if websocket_connections:
        message = {"type": event_type, "data": data, "timestamp": time.time()}
        for connection in websocket_connections.copy():
            try:
                await connection.send_json(message)
            except:
                websocket_connections.remove(connection)

# WebSocket Routes
from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    """WebSocket endpoint for real-time notifications"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "data": {"message": "🔔 Real-time notifications active"},
            "timestamp": time.time()
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

@router.get("/notifications/recent")
async def get_recent_notifications(user: dict = Depends(get_current_user)):
    """Get recent notifications for the user"""
    notifications = [
        {
            "id": f"notif_{i}",
            "type": "matter_update" if i % 3 == 0 else "document_processed" if i % 3 == 1 else "task_deadline",
            "title": "Matter Progress Update" if i % 3 == 0 else "Document Processed" if i % 3 == 1 else "Task Deadline",
            "message": f"Matter {2000 + i} has been updated to 'In Progress' status" if i % 3 == 0 
                      else f"Document '{['Contract', 'LLC1', 'CON29'][i % 3]}.pdf' has been processed" if i % 3 == 1
                      else f"Task 'Review {['Planning', 'Legal', 'Financial'][i % 3]} Documents' is due in 2 hours",
            "timestamp": time.time() - (i * 1800),  # 30 minutes intervals
            "read": i > 5,
            "priority": "high" if i < 3 else "normal",
            "action_url": f"/matters/{2000 + i}" if i % 3 == 0 else f"/documents" if i % 3 == 1 else f"/tasks",
            "icon": "📋" if i % 3 == 0 else "📄" if i % 3 == 1 else "⏰"
        } for i in range(12)
    ]
    
    return {"notifications": notifications}

# ==================== AI-POWERED DOCUMENT ANALYSIS ENGINE ====================

@router.post("/ai/document/analyze")
async def analyze_document(
    file: UploadFile,
    matter_id: str = Form(...),
    user: dict = Depends(get_current_user)
):
    """AI-powered document analysis with OCR, extraction, and risk assessment"""
    
    # Read file content
    content = await file.read()
    
    # Simulate AI processing
    analysis = {
        "document_id": f"doc_{int(time.time())}",
        "filename": file.filename,
        "file_size": len(content),
        "matter_id": matter_id,
        "processing_status": "completed",
        "extracted_data": {
            "property_address": "15 High Street, Bishop's Stortford, Hertfordshire, CM23 2LS",
            "postcode": "CM23 2LS",
            "council": "East Hertfordshire District Council",
            "property_type": "Residential Freehold",
            "title_number": "HD123456",
            "planning_references": ["3/19/1234/FUL", "3/20/0567/HH"],
            "conservation_area": True,
            "listed_building": False,
            "flood_zone": "Zone 1 (Low Risk)",
            "contamination_risk": "Low",
            "mining_risk": "Low",
            "radon_level": "Below Action Level"
        },
        "ai_summary": f"This {'LLC1' if 'llc1' in file.filename.lower() else 'CON29'} search reveals a residential freehold property in a conservation area with low environmental risks. No significant planning constraints identified beyond conservation area requirements. The property appears suitable for standard residential mortgage lending with no unusual risks detected.",
        "risk_assessment": {
            "overall_risk": "Low-Medium",
            "risk_score": 0.35,
            "risks": [
                {
                    "category": "Planning",
                    "risk": "Conservation Area Restrictions", 
                    "level": "Medium",
                    "description": "Property is within a conservation area - planning permission required for most external alterations",
                    "recommendation": "Advise client of conservation area restrictions and potential planning requirements"
                },
                {
                    "category": "Environmental",
                    "risk": "Flood Risk",
                    "level": "Low", 
                    "description": "Property is in Flood Zone 1 with minimal flood risk",
                    "recommendation": "Standard home insurance should be sufficient"
                }
            ]
        },
        "timeline_prediction": {
            "estimated_exchange": "4-6 weeks",
            "estimated_completion": "6-8 weeks",
            "confidence": 0.85,
            "factors": [
                "Standard residential transaction",
                "No complex planning issues",
                "Low environmental risk",
                "Experienced council (East Herts - typical 10-14 day turnaround)"
            ]
        },
        "compliance_checks": {
            "aml_required": True,
            "source_of_funds": "Required for purchases over £100k",
            "insurance_requirements": ["Buildings insurance", "Professional indemnity"],
            "regulatory_flags": []
        },
        "coordinates": {
            "lat": 51.8721,
            "lng": 0.1604,
            "accuracy": "high"
        }
    }
    
    return analysis

@router.get("/ai/document/{document_id}/summary")
async def get_document_summary(document_id: str, user: dict = Depends(get_current_user)):
    """Get AI-generated document summary"""
    
    summaries = {
        "contract": "This residential sale contract is for a £485,000 freehold property. Key terms include: 10% deposit, 4-week exchange period, standard conditions of sale. No unusual clauses identified. Property sold with vacant possession. All standard warranties and undertakings present.",
        "llc1": "LLC1 search confirms no local land charges registered against the property. Clean title with no planning enforcement notices, no tree preservation orders affecting the property boundary, and no financial charges. Property is within conservation area CA/15 - advise client of restrictions on external alterations.",
        "con29": "CON29 environmental search shows low risk profile. Property in Flood Zone 1, no contaminated land designation, no mining subsidence risk. Planning history shows two minor applications approved in last 5 years. Highways: road is adopted, no outstanding road charges. CIL liability: £2,400 (paid by seller).",
        "title_deeds": "Registered freehold title with good root of title dating to 1987. No restrictive covenants affecting use. Two rights of way noted: pedestrian access to rear gardens and utility company wayleave. No mortgages or charges registered. Boundaries clearly defined with no disputes recorded."
    }
    
    doc_type = "llc1" if "llc1" in document_id.lower() else "con29" if "con29" in document_id.lower() else "contract"
    
    return {
        "document_id": document_id,
        "summary": summaries.get(doc_type, summaries["contract"]),
        "key_points": [
            "No significant legal obstacles identified",
            "Property suitable for mortgage lending", 
            "Standard residential transaction terms",
            "Conservation area requires planning awareness"
        ],
        "action_items": [
            "Advise client of conservation area restrictions",
            "Arrange buildings insurance before exchange",
            "Confirm completion arrangements with seller's solicitor",
            "Prepare exchange documentation"
        ],
        "confidence": 0.92
    }

@router.post("/ai/property/geocode")
async def geocode_property(address: str = Form(...), user: dict = Depends(get_current_user)):
    """Geocode property address for mapping"""
    
    # Simulate geocoding (in real implementation, use Google Maps API, etc.)
    mock_locations = {
        "bishop": {"lat": 51.8721, "lng": 0.1604, "accuracy": "high"},
        "hertford": {"lat": 51.7963, "lng": -0.0791, "accuracy": "high"},
        "cambridge": {"lat": 52.2053, "lng": 0.1218, "accuracy": "high"},
        "london": {"lat": 51.5074, "lng": -0.1278, "accuracy": "medium"}
    }
    
    # Find best match
    address_lower = address.lower()
    location = mock_locations.get("bishop")  # default
    
    for key, loc in mock_locations.items():
        if key in address_lower:
            location = loc
            break
    
    return {
        "address": address,
        "coordinates": location,
        "nearby_amenities": [
            {"type": "school", "name": "Bishop's Stortford High School", "distance": "0.3 miles"},
            {"type": "transport", "name": "Bishop's Stortford Station", "distance": "0.5 miles"},
            {"type": "shopping", name: "Jackson Square", "distance": "0.2 miles"},
            {"type": "medical", "name": "Herts & Essex Hospital", "distance": "1.2 miles"}
        ],
        "local_insights": {
            "average_house_price": "£465,000",
            "price_trend": "+3.2% last 12 months",
            "crime_rate": "Below national average",
            "school_ratings": "Good to Outstanding",
            "transport_links": "Direct trains to London Liverpool Street (35 mins)"
        }
    }

@router.post("/notifications/{notification_id}/mark-read")
async def mark_notification_read(notification_id: str, user: dict = Depends(get_current_user)):
    """Mark a notification as read"""
    return {"status": "success", "message": f"Notification {notification_id} marked as read"}

# ==================== AI HELPBOT ASSISTANT ====================

@router.post("/ai/helpbot/chat")
async def helpbot_chat(
    message: str = Form(...),
    context: str = Form(""),
    user: dict = Depends(get_current_user)
):
    """AI Helpbot that can help navigate the platform and answer questions"""
    
    message_lower = message.lower()
    
    # Smart responses based on user queries
    if any(word in message_lower for word in ["upload", "document", "file"]):
        response = {
            "message": "I can help you upload documents! 📄 Go to the Documents page and either:\n\n• Click the 'Upload Documents' button\n• Drag and drop files directly onto the page\n• Use the bulk upload feature for multiple files\n\nThe AI will automatically analyze your documents and extract key information like addresses, risks, and compliance requirements. Would you like me to show you the documents page?",
            "actions": [
                {"label": "Go to Documents", "action": "navigate", "target": "documents"},
                {"label": "Learn about AI Analysis", "action": "explain", "topic": "ai_analysis"}
            ]
        }
    elif any(word in message_lower for word in ["matter", "case", "property"]):
        response = {
            "message": "I can help with matter management! 📋 Here's what you can do:\n\n• **Create New Matter**: Click 'New Matter' to start a new property transaction\n• **View Progress**: Check timeline predictions and completion estimates\n• **Track Deadlines**: See upcoming tasks and deadlines\n• **Client Updates**: Send automated progress updates\n\nWould you like to create a new matter or view existing ones?",
            "actions": [
                {"label": "Create New Matter", "action": "navigate", "target": "matters?action=create"},
                {"label": "View All Matters", "action": "navigate", "target": "matters"}
            ]
        }
    elif any(word in message_lower for word in ["search", "find", "lookup"]):
        response = {
            "message": "I can help you search! 🔍 Use the global search box at the top to find:\n\n• **Matters** by reference, client name, or address\n• **Documents** by filename or content\n• **Tasks** by description or deadline\n• **Communications** by contact or subject\n\nJust type what you're looking for and I'll show intelligent suggestions. You can also use filters to narrow down results!",
            "actions": [
                {"label": "Focus Search Box", "action": "focus", "target": "global-search"},
                {"label": "Show Search Tips", "action": "explain", "topic": "search_tips"}
            ]
        }
    elif any(word in message_lower for word in ["ai", "analysis", "risk", "summary"]):
        response = {
            "message": "Our AI Analysis is incredibly powerful! 🤖 Here's what it does:\n\n• **Document Analysis**: Extracts addresses, risks, compliance requirements\n• **Risk Assessment**: Scores properties and identifies potential issues\n• **Timeline Prediction**: Estimates exchange and completion dates\n• **Smart Summaries**: Creates plain English summaries of complex documents\n• **Property Mapping**: Shows properties on interactive maps with local insights\n\nWant to see it in action? Upload a document and watch the magic happen!",
            "actions": [
                {"label": "Try AI Analysis", "action": "navigate", "target": "documents"},
                {"label": "View AI Dashboard", "action": "navigate", "target": "dashboard"}
            ]
        }
    elif any(word in message_lower for word in ["calendar", "deadline", "appointment"]):
        response = {
            "message": "Let me help with scheduling! 📅 The calendar system can:\n\n• **Track Deadlines**: All matter deadlines automatically added\n• **Team Scheduling**: See who's available when\n• **Client Appointments**: Schedule and manage client meetings\n• **Court Dates**: Track important legal deadlines\n• **Automated Reminders**: Get notified before important dates\n\nWould you like to view your calendar or create a new event?",
            "actions": [
                {"label": "Open Calendar", "action": "navigate", "target": "calendar"},
                {"label": "Create Event", "action": "navigate", "target": "calendar?action=create"}
            ]
        }
    elif any(word in message_lower for word in ["client", "communication", "portal"]):
        response = {
            "message": "Client communication made easy! 💬 Here's how:\n\n• **Secure Messaging**: Send encrypted messages to clients\n• **Progress Updates**: Automated status updates\n• **Document Sharing**: Secure document exchange\n• **Client Portal**: Clients can log in to view progress\n• **Mobile Friendly**: Works on all devices\n\nWant to send a client update or access the communications hub?",
            "actions": [
                {"label": "Open Communications", "action": "navigate", "target": "communications"},
                {"label": "Client Portal Setup", "action": "explain", "topic": "client_portal"}
            ]
        }
    elif any(word in message_lower for word in ["help", "how", "tutorial", "guide"]):
        response = {
            "message": "I'm here to help! 😊 Here are the main things I can assist with:\n\n• **Navigation**: Finding any page or feature\n• **Document Management**: Uploading, analyzing, organizing files\n• **Matter Management**: Creating, tracking, updating cases\n• **AI Features**: Understanding our intelligent analysis tools\n• **Client Communication**: Setting up portals and messaging\n• **Reporting**: Generating insights and analytics\n\nWhat would you like to learn about? Just ask me anything!",
            "actions": [
                {"label": "Platform Tour", "action": "tour", "target": "full"},
                {"label": "Quick Start Guide", "action": "explain", "topic": "quick_start"}
            ]
        }
    else:
        response = {
            "message": f"I understand you're asking about '{message}'. I'm your AI assistant and I can help with:\n\n• **Document Analysis & Upload** 📄\n• **Matter & Case Management** 📋\n• **Global Search & Filtering** 🔍\n• **Calendar & Deadlines** 📅\n• **Client Communications** 💬\n• **AI Features & Analytics** 🤖\n\nCould you tell me more specifically what you'd like help with?",
            "actions": [
                {"label": "Show All Features", "action": "tour", "target": "features"},
                {"label": "Common Tasks", "action": "explain", "topic": "common_tasks"}
            ]
        }
    
    return {
        "response": response["message"],
        "actions": response.get("actions", []),
        "timestamp": time.time(),
        "context_understood": True,
        "suggested_followups": [
            "How do I upload documents?",
            "Show me the AI analysis features",
            "Help me create a new matter",
            "What can the calendar do?"
        ]
    }

@router.get("/ai/helpbot/suggestions")
async def get_helpbot_suggestions(page: str = "", user: dict = Depends(get_current_user)):
    """Get contextual suggestions based on current page"""
    
    suggestions = {
        "dashboard": [
            "How do I create a new matter?",
            "Show me recent document uploads",
            "What are the AI analytics?",
            "Help me understand the metrics"
        ],
        "matters": [
            "How do I add documents to a matter?",
            "Can I set up automated deadlines?",
            "How does timeline prediction work?",
            "Show me client communication options"
        ],
        "documents": [
            "What documents can the AI analyze?",
            "How accurate is the extraction?",
            "Can I bulk upload documents?",
            "How do I view AI summaries?"
        ],
        "calendar": [
            "How do I set up deadline reminders?",
            "Can I share calendars with colleagues?",
            "How does team scheduling work?",
            "Set up client appointment booking"
        ]
    }
    
    return {
        "page": page,
        "suggestions": suggestions.get(page, suggestions["dashboard"]),
        "quick_actions": [
            {"label": "Upload Document", "action": "navigate", "target": "documents"},
            {"label": "Create Matter", "action": "navigate", "target": "matters?action=create"},
            {"label": "View Calendar", "action": "navigate", "target": "calendar"},
            {"label": "Search Everything", "action": "focus", "target": "global-search"}
        ]
    }

# ==================== ADVANCED SEARCH & FILTERING SYSTEM ====================

@router.get("/search/global")
async def global_search(
    q: str = Query(..., description="Search query"),
    filters: str = Query("", description="JSON filters"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user)
):
    """Global intelligent search across all platform data"""
    
    # Simulate intelligent search results
    results = {
        "query": q,
        "total_results": 45,
        "search_time": 0.089,
        "results": [
            {
                "type": "matter",
                "id": "MTR2024001",
                "title": "15 High Street, Bishop's Stortford",
                "subtitle": "Residential Purchase • £485,000 • Exchange: 2 weeks",
                "content": "Freehold property purchase for Mr & Mrs Johnson. Conservation area property with clean title. AI Risk Score: Low-Medium (0.35)",
                "url": "/matters/MTR2024001",
                "icon": "📋",
                "relevance": 0.95,
                "highlights": ["High Street", "Bishop's Stortford"],
                "metadata": {
                    "client": "Johnson Family",
                    "value": "£485,000",
                    "status": "Pre-exchange",
                    "risk_score": 0.35
                }
            },
            {
                "type": "document", 
                "id": "DOC2024156",
                "title": "LLC1 Search - High Street Property",
                "subtitle": "Uploaded 3 days ago • AI Analyzed • 12 pages",
                "content": "Local land charges search confirming conservation area designation. No planning enforcement notices. Clean title with standard residential use.",
                "url": "/documents/DOC2024156",
                "icon": "📄",
                "relevance": 0.92,
                "highlights": ["High Street", "conservation area"],
                "metadata": {
                    "file_type": "PDF",
                    "ai_confidence": 0.94,
                    "risk_flags": 1,
                    "pages": 12
                }
            },
            {
                "type": "communication",
                "id": "MSG2024089",
                "title": "Client Query - Planning Permission",
                "subtitle": "From: sarah.johnson@email.com • 1 day ago",
                "content": "Hi, we wanted to check if we'll need planning permission for the conservatory extension we discussed...",
                "url": "/communications/MSG2024089", 
                "icon": "💬",
                "relevance": 0.78,
                "highlights": ["planning permission"],
                "metadata": {
                    "sender": "Sarah Johnson",
                    "status": "unread",
                    "priority": "medium"
                }
            },
            {
                "type": "task",
                "id": "TSK2024045",
                "title": "Review Planning History",
                "subtitle": "Due: Tomorrow • Assigned: John Smith",
                "content": "Check planning applications for High Street property and advise on conservation area restrictions for client extension plans.",
                "url": "/tasks/TSK2024045",
                "icon": "✅",
                "relevance": 0.86,
                "highlights": ["Planning", "High Street"],
                "metadata": {
                    "assignee": "John Smith",
                    "due_date": "2025-09-13",
                    "priority": "high",
                    "status": "in_progress"
                }
            }
        ],
        "filters_applied": [],
        "suggested_filters": [
            {"type": "matter_status", "values": ["active", "completed", "pending"]},
            {"type": "document_type", "values": ["LLC1", "CON29", "Contract", "Title Deeds"]},
            {"type": "risk_level", "values": ["low", "medium", "high"]},
            {"type": "date_range", "values": ["today", "this_week", "this_month", "this_year"]}
        ],
        "smart_suggestions": [
            "15 High Street property documents",
            "Johnson family matters", 
            "Conservation area properties",
            "Planning permission queries",
            "High risk matters"
        ]
    }
    
    return results

@router.get("/search/suggestions")
async def search_suggestions(q: str = Query(...), user: dict = Depends(get_current_user)):
    """Get intelligent search suggestions as user types"""
    
    suggestions = [
        {"text": f"{q} documents", "type": "documents", "count": 12},
        {"text": f"{q} matters", "type": "matters", "count": 5},
        {"text": f"{q} communications", "type": "communications", "count": 8},
        {"text": f"High Street, {q}", "type": "address", "count": 3},
        {"text": f"{q} planning applications", "type": "planning", "count": 2}
    ]
    
    return {"query": q, "suggestions": suggestions[:5]}

@router.post("/search/save")
async def save_search(
    name: str = Form(...),
    query: str = Form(...),
    filters: str = Form("{}"),
    user: dict = Depends(get_current_user)
):
    """Save a search for future use"""
    
    saved_search = {
        "id": f"search_{int(time.time())}",
        "name": name,
        "query": query,
        "filters": filters,
        "created_at": time.time(),
        "user_id": user["sub"]
    }
    
    return {"status": "success", "search": saved_search}

@router.get("/search/saved")
async def get_saved_searches(user: dict = Depends(get_current_user)):
    """Get user's saved searches"""
    
    saved_searches = [
        {
            "id": "search_1",
            "name": "High Risk Matters",
            "query": "risk:high status:active",
            "result_count": 12,
            "created_at": time.time() - 86400
        },
        {
            "id": "search_2", 
            "name": "Conservation Area Properties",
            "query": "conservation area type:matter",
            "result_count": 8,
            "created_at": time.time() - 172800
        },
        {
            "id": "search_3",
            "name": "Pending Planning Applications",
            "query": "planning status:pending",
            "result_count": 259200
        }
    ]
    
    return {"searches": saved_searches}

# ==================== AI-POWERED DOCUMENT ANALYSIS ENGINE ====================

@router.post("/ai/document-analysis")
async def ai_document_analysis(
    file: UploadFile, 
    user: dict = Depends(get_current_user)
):
    """
    🤖 AI-Powered Document Analysis Engine
    
    Advanced document processing with:
    - OCR and text extraction
    - Legal risk assessment 
    - Timeline predictions
    - Automated compliance checking
    - Property address extraction
    """
    
    # Read the uploaded file
    contents = await file.read()
    
    # Simulate AI processing
    import re
    import random
    
    # Basic text extraction simulation
    text_content = f"Sample extracted text from {file.filename}..."
    
    # Property address extraction
    addresses = [
        "123 High Street, Cambridge, CB1 2AB",
        "45 Oak Avenue, London, SW1A 1AA", 
        "78 Church Lane, Manchester, M1 4BD",
        "12 Market Square, Bristol, BS1 5QD"
    ]
    
    extracted_address = random.choice(addresses)
    
    # AI Risk Assessment
    risk_factors = [
        {"type": "flood_risk", "level": "medium", "confidence": 0.85, "description": "Property located in Environment Agency Flood Zone 2"},
        {"type": "conservation_area", "level": "high", "confidence": 0.92, "description": "Property within designated Conservation Area - planning restrictions apply"},
        {"type": "listed_building", "level": "medium", "confidence": 0.78, "description": "Potential Listed Building status detected - requires verification"},
        {"type": "road_adoption", "level": "low", "confidence": 0.95, "description": "Highway appears to be adopted by local authority"},
        {"type": "ground_conditions", "level": "medium", "confidence": 0.67, "description": "Geological survey may be recommended based on area characteristics"}
    ]
    
    # Timeline Predictions  
    predicted_timeline = {
        "search_completion": "7-10 days",
        "exchange_ready": "4-6 weeks", 
        "completion_estimate": "6-8 weeks",
        "confidence": 0.82,
        "factors": [
            "Standard residential transaction",
            "No complex ownership structures detected",
            "Council search times: average for area"
        ]
    }
    
    # Cost Predictions
    cost_estimate = {
        "searches": {"min": 450, "max": 650, "confidence": 0.88},
        "additional_enquiries": {"min": 200, "max": 400, "confidence": 0.75},
        "indemnity_insurance": {"min": 0, "max": 300, "confidence": 0.60},
        "total_estimate": {"min": 650, "max": 1350}
    }
    
    # Compliance Checklist
    compliance_items = [
        {"item": "Local Land Charges Search", "status": "required", "priority": "high"},
        {"item": "Environmental Search", "status": "recommended", "priority": "medium"},
        {"item": "Water Authority Search", "status": "required", "priority": "high"},
        {"item": "Mining Search", "status": "not_required", "priority": "low"},
        {"item": "Chancel Repair Liability", "status": "check_required", "priority": "medium"}
    ]
    
    # Document Classification
    doc_classification = {
        "document_type": "property_search" if "search" in file.filename.lower() else "legal_document",
        "confidence": 0.91,
        "pages_detected": random.randint(3, 25),
        "quality_score": 0.88,
        "processing_method": "hybrid_ai_ocr"
    }
    
    return {
        "analysis_id": f"ai_analysis_{int(time.time())}",
        "document_info": {
            "filename": file.filename,
            "size_mb": round(len(contents) / (1024 * 1024), 2),
            "classification": doc_classification
        },
        "extracted_data": {
            "property_address": extracted_address,
            "text_length": len(text_content),
            "key_phrases": ["conservation area", "flood zone", "highway adoption", "planning permission"],
            "confidence_score": 0.87
        },
        "ai_risk_assessment": {
            "overall_risk_score": 0.65,
            "risk_level": "Medium",
            "factors": risk_factors
        },
        "timeline_prediction": predicted_timeline,
        "cost_estimation": cost_estimate,
        "compliance_checklist": compliance_items,
        "recommendations": [
            "Obtain Environmental Search due to flood risk indicators",
            "Verify Conservation Area restrictions with planning department", 
            "Consider indemnity insurance for any title defects",
            "Standard searches package recommended for this property type"
        ],
        "processing_time_ms": random.randint(850, 1200),
        "ai_confidence": 0.84
    }

@router.get("/ai/search")
async def ai_intelligent_search(
    query: str,
    filters: str = "all",
    user: dict = Depends(get_current_user)
):
    """
    🔍 AI-Powered Intelligent Search
    
    Semantic search across all platform data with:
    - Natural language query processing
    - Cross-reference matching
    - Intelligent filters and suggestions
    """
    
    # Simulate intelligent search results
    search_results = {
        "query_analysis": {
            "original_query": query,
            "interpreted_intent": f"Searching for conveyancing matters related to: {query}",
            "suggested_filters": ["recent", "high_priority", "similar_properties"],
            "confidence": 0.89
        },
        "results": {
            "matters": [
                {
                    "id": "matter_2001",
                    "ref": "CV/2025/2001", 
                    "property": "123 High Street, Cambridge",
                    "status": "searches_in_progress",
                    "relevance": 0.92,
                    "match_reason": "Property address similarity"
                },
                {
                    "id": "matter_2002", 
                    "ref": "CV/2025/2002",
                    "property": "45 Oak Avenue, London",
                    "status": "exchange_ready",
                    "relevance": 0.87,
                    "match_reason": "Similar search results"
                }
            ],
            "documents": [
                {
                    "id": "doc_501",
                    "filename": "Local_Search_Cambridge.pdf",
                    "matter_ref": "CV/2025/2001",
                    "relevance": 0.95,
                    "match_reason": "Content similarity detected"
                }
            ],
            "suggestions": [
                "flood risk cambridge",
                "conservation area restrictions", 
                "local authority searches"
            ]
        },
        "total_results": 15,
        "search_time_ms": 234
    }
    
    return search_results

@router.post("/ai/property-mapping")
async def ai_property_mapping(
    address: str,
    user: dict = Depends(get_current_user)
):
    """
    🗺️ AI Property Mapping System
    
    Generate mapping data for properties including:
    - Geocoding from address
    - Boundary identification  
    - Environmental overlays
    - Planning constraints
    """
    
    # Simulate geocoding and mapping data
    import random
    
    # UK coordinates for demo
    base_coords = {
        "cambridge": {"lat": 52.2053, "lng": 0.1218},
        "london": {"lat": 51.5074, "lng": -0.1278}, 
        "manchester": {"lat": 53.4808, "lng": -2.2426},
        "bristol": {"lat": 51.4545, "lng": -2.5879}
    }
    
    # Select coordinates based on address
    city_key = next((k for k in base_coords.keys() if k.lower() in address.lower()), "cambridge")
    base_coord = base_coords[city_key]
    
    # Add random offset for specific property
    property_coords = {
        "latitude": base_coord["lat"] + random.uniform(-0.01, 0.01),
        "longitude": base_coord["lng"] + random.uniform(-0.01, 0.01)
    }
    
    mapping_data = {
        "address": address,
        "coordinates": property_coords,
        "geocoding_confidence": 0.94,
        "property_boundaries": {
            "area_sqm": random.randint(200, 800),
            "boundary_confidence": 0.87,
            "source": "ordnance_survey"
        },
        "environmental_layers": {
            "flood_zones": {
                "zone": random.choice(["1", "2", "3"]),
                "risk_level": random.choice(["low", "medium", "high"])
            },
            "conservation_areas": {
                "within_area": random.choice([True, False]),
                "area_name": "Historic Town Centre" if random.choice([True, False]) else None
            },
            "tree_preservation": {
                "tpo_present": random.choice([True, False]),
                "protected_trees": random.randint(0, 5)
            }
        },
        "planning_constraints": [
            {"type": "conservation_area", "impact": "medium", "description": "Planning applications require special consideration"},
            {"type": "archaeological_area", "impact": "low", "description": "Archaeological watching brief may be required"}
        ],
        "nearby_features": [
            {"type": "school", "name": "Local Primary School", "distance_m": 420},
            {"type": "transport", "name": "Railway Station", "distance_m": 850},
            {"type": "shopping", "name": "Town Centre", "distance_m": 650}
        ]
    }
    
    return mapping_data

@router.post("/ai/helpbot")
async def ai_helpbot_query(
    message: str,
    context: str = "general",
    user: dict = Depends(get_current_user)
):
    """
    🤖 AI Helpbot Assistant
    
    Intelligent assistance for platform navigation and conveyancing guidance:
    - Natural language query processing
    - Context-aware responses
    - Platform navigation help
    - Legal guidance and explanations
    """
    
    # Simulate AI processing of user query
    query_lower = message.lower()
    
    # Context-aware responses based on query content
    if any(word in query_lower for word in ["search", "find", "look"]):
        response = {
            "message": "I can help you search across the platform! Use the search box at the top to find matters, documents, or users. You can also try natural language queries like 'show me matters in Cambridge' or 'find flood risk documents'.",
            "suggested_actions": [
                {"text": "Try Advanced Search", "action": "open_search", "icon": "🔍"},
                {"text": "Search Recent Matters", "action": "search_matters", "icon": "📋"},
                {"text": "Find Documents", "action": "search_documents", "icon": "📄"}
            ],
            "type": "guidance"
        }
    elif any(word in query_lower for word in ["upload", "document", "file"]):
        response = {
            "message": "To upload documents, go to the Documents page and drag & drop files into the upload area. Our AI will automatically analyze them for risks, extract property details, and suggest next steps.",
            "suggested_actions": [
                {"text": "Go to Documents", "action": "show_documents", "icon": "📄"},
                {"text": "View Upload Guide", "action": "show_upload_help", "icon": "📤"},
                {"text": "AI Analysis Info", "action": "show_ai_help", "icon": "🤖"}
            ],
            "type": "instruction"
        }
    elif any(word in query_lower for word in ["risk", "assessment", "analysis"]):
        response = {
            "message": "Our AI Risk Assessment analyzes documents for flood zones, conservation areas, planning restrictions, and other conveyancing risks. Risk scores range from Low to High with confidence ratings.",
            "suggested_actions": [
                {"text": "View Risk Dashboard", "action": "show_risks", "icon": "⚠️"},
                {"text": "Learn About Risks", "action": "show_risk_guide", "icon": "📚"},
                {"text": "Run Risk Analysis", "action": "analyze_document", "icon": "🔍"}
            ],
            "type": "explanation"
        }
    elif any(word in query_lower for word in ["timeline", "prediction", "completion"]):
        response = {
            "message": "AI Timeline Predictions estimate matter completion based on property type, searches required, and historical data. Typical residential transactions complete in 6-8 weeks.",
            "suggested_actions": [
                {"text": "View Timeline", "action": "show_timeline", "icon": "⏱️"},
                {"text": "Matter Progress", "action": "show_progress", "icon": "📊"},
                {"text": "Update Estimate", "action": "update_timeline", "icon": "🔄"}
            ],
            "type": "information"
        }
    elif any(word in query_lower for word in ["map", "property", "location"]):
        response = {
            "message": "Property Mapping shows exact locations with environmental overlays, flood zones, conservation areas, and nearby features. Click any property address to view its map.",
            "suggested_actions": [
                {"text": "Open Map View", "action": "show_map", "icon": "🗺️"},
                {"text": "Search by Location", "action": "search_location", "icon": "📍"},
                {"text": "View Overlays", "action": "show_overlays", "icon": "🌍"}
            ],
            "type": "feature"
        }
    else:
        response = {
            "message": "I'm here to help with your conveyancing platform! I can assist with document analysis, risk assessment, timeline predictions, property mapping, and general navigation. What would you like to know?",
            "suggested_actions": [
                {"text": "Platform Tour", "action": "start_tour", "icon": "🎯"},
                {"text": "Common Tasks", "action": "show_tasks", "icon": "✅"},
                {"text": "AI Features", "action": "show_ai_features", "icon": "🤖"},
                {"text": "Contact Support", "action": "contact_support", "icon": "💬"}
            ],
            "type": "general"
        }
    
    return {
        "query": message,
        "response": response,
        "context": context,
        "timestamp": time.time(),
        "session_id": f"helpbot_{int(time.time())}"
    }

@router.post("/ai/document-summary")
async def ai_document_summary(
    document_id: str,
    user: dict = Depends(get_current_user)
):
    """
    📝 AI Document Summarization
    
    Generate intelligent summaries of legal documents:
    - Key points extraction
    - Risk highlights
    - Action items identification
    - Plain English explanations
    """
    
    # Simulate AI document summarization
    summary_data = {
        "document_id": document_id,
        "summary": {
            "executive_summary": "This Local Land Charges search reveals a residential property in a Conservation Area with moderate flood risk. No significant legal obstacles identified, but planning restrictions apply for any future alterations.",
            
            "key_findings": [
                {
                    "category": "Planning & Development",
                    "items": [
                        "Property located within Historic Town Centre Conservation Area",
                        "Article 4 Direction applies - permitted development rights restricted",
                        "No enforcement notices or planning contravention identified"
                    ],
                    "impact": "medium"
                },
                {
                    "category": "Environmental Factors", 
                    "items": [
                        "Environment Agency Flood Zone 2 - medium probability flooding",
                        "No contaminated land designations",
                        "Standard radon risk area"
                    ],
                    "impact": "medium"
                },
                {
                    "category": "Highways & Access",
                    "items": [
                        "Abutting highway adopted and maintained at public expense",
                        "No proposed highway works affecting the property",
                        "Standard vehicular access rights confirmed"
                    ],
                    "impact": "low"
                }
            ],
            
            "risk_highlights": [
                {
                    "risk": "Conservation Area Restrictions",
                    "level": "Medium",
                    "description": "Future alterations will require Conservation Area consent in addition to standard planning permission",
                    "recommendation": "Advise client of restricted permitted development rights"
                },
                {
                    "risk": "Flood Risk Zone 2", 
                    "level": "Medium",
                    "description": "Property has medium probability of flooding, may affect insurance and mortgageability",
                    "recommendation": "Recommend flood risk assessment and appropriate insurance coverage"
                }
            ],
            
            "action_items": [
                {
                    "priority": "high",
                    "task": "Obtain Environmental Search to assess flood risk in detail",
                    "deadline": "Within 5 working days"
                },
                {
                    "priority": "medium", 
                    "task": "Advise client of Conservation Area implications for future works",
                    "deadline": "Before exchange of contracts"
                },
                {
                    "priority": "medium",
                    "task": "Verify flood insurance availability with client's insurer",
                    "deadline": "Before exchange of contracts"
                }
            ],
            
            "plain_english_explanation": "This property search shows the house is in a historic area with some restrictions on changes you can make, and there's a medium chance of flooding. The road is properly maintained by the council. Overall, it's a fairly typical result with some standard precautions needed.",
            
            "compliance_status": {
                "mandatory_searches": "Complete",
                "recommended_searches": "Environmental search outstanding", 
                "legal_requirements": "Standard requirements met",
                "overall_status": "Proceeding - minor items to resolve"
            }
        },
        
        "ai_analysis": {
            "processing_method": "advanced_nlp_analysis",
            "confidence_score": 0.91,
            "document_complexity": "standard",
            "processing_time_ms": 1247,
            "ai_model_version": "domus-legal-ai-v2.1"
        }
    }
    
    return summary_data

# Export the router
enterprise_router = router

# Create FastAPI app and include router
if __name__ == "__main__":
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    import uvicorn
    
    app = FastAPI(
        title="Domus Conveyancing Enterprise API",
        description="Comprehensive enterprise conveyancing platform API",
        version="2.0.0"
    )
    
    # Mount static files for frontend
    app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
    
    # Include the enterprise router
    app.include_router(router, prefix="/api")
    
    # Redirect root to frontend
    @app.get("/")
    async def root():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/frontend/index.html")
    
    print("🚀 Starting Domus Conveyancing Enterprise Platform...")
    print("📊 Frontend available at: http://localhost:8000")
    print("🔧 API documentation at: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)