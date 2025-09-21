"""
Comprehensive Regulatory Services Data Models
Supporting: Planning, Building Control, Land Charges, Waste Regulatory, Private Sector Housing
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

# ============================================================================
# PLANNING APPLICATIONS (Enhanced)
# ============================================================================

class PlanningApplicationType(str, Enum):
    HOUSEHOLDER = "Householder"
    FULL_PLANNING = "Full Planning"
    OUTLINE_PLANNING = "Outline Planning"
    RESERVED_MATTERS = "Reserved Matters"
    LISTED_BUILDING = "Listed Building Consent"
    CONSERVATION_AREA = "Conservation Area Consent"
    ADVERTISEMENT = "Advertisement Consent"
    CHANGE_OF_USE = "Change of Use"
    PRIOR_APPROVAL = "Prior Approval"
    LAWFUL_DEVELOPMENT = "Certificate of Lawful Development"

class PlanningStatus(str, Enum):
    RECEIVED = "Received"
    VALIDATION = "Under Validation"
    CONSULTATION = "Public Consultation"
    ASSESSMENT = "Under Assessment" 
    COMMITTEE = "Planning Committee"
    DECISION_DUE = "Decision Due"
    APPROVED = "Approved"
    REFUSED = "Refused"
    WITHDRAWN = "Withdrawn"
    APPEALED = "Appealed"

class PlanningApplication(BaseModel):
    id: str = Field(..., description="Planning application reference")
    application_type: PlanningApplicationType
    status: PlanningStatus
    site_address: str
    applicant_name: str
    applicant_address: str
    agent_name: Optional[str] = None
    agent_address: Optional[str] = None
    description: str = Field(..., description="Development description")
    parish: Optional[str] = None
    ward: str
    case_officer: str
    date_received: date
    date_validated: Optional[date] = None
    consultation_start: Optional[date] = None
    consultation_end: Optional[date] = None
    target_decision_date: date
    actual_decision_date: Optional[date] = None
    decision: Optional[str] = None
    appeal_reference: Optional[str] = None
    conditions: Optional[List[str]] = []
    documents: List[str] = []
    consultations_sent: List[str] = []
    public_comments: int = 0
    site_visit_required: bool = False
    committee_required: bool = False
    environmental_assessment: bool = False
    tree_preservation_order: bool = False
    listed_building_affected: bool = False
    conservation_area: bool = False
    green_belt: bool = False
    flood_zone: Optional[str] = None

# ============================================================================
# BUILDING CONTROL (Enhanced)
# ============================================================================

class BuildingControlType(str, Enum):
    FULL_PLANS = "Full Plans Application"
    BUILDING_NOTICE = "Building Notice"
    REGULARISATION = "Regularisation Application"
    DEMOLITION = "Demolition Notice"
    DANGEROUS_STRUCTURE = "Dangerous Structure"

class BuildingControlStage(str, Enum):
    APPLICATION_RECEIVED = "Application Received"
    PLANS_APPROVED = "Plans Approved"
    WORK_COMMENCED = "Work Commenced"
    FOUNDATION_INSPECTION = "Foundation Inspection"
    DPC_INSPECTION = "DPC Inspection"
    DRAINAGE_INSPECTION = "Drainage Inspection"
    INSULATION_INSPECTION = "Insulation Inspection"
    FINAL_INSPECTION = "Final Inspection"
    COMPLETION_CERTIFICATE = "Completion Certificate Issued"
    COMPLIANCE_NOTICE = "Compliance Notice Issued"

class BuildingControlApplication(BaseModel):
    id: str = Field(..., description="Building control reference")
    application_type: BuildingControlType
    stage: BuildingControlStage
    site_address: str
    applicant_name: str
    applicant_contact: str
    description: str = Field(..., description="Work description")
    estimated_cost: Optional[float] = None
    floor_area: Optional[float] = None
    date_received: date
    date_approved: Optional[date] = None
    commencement_date: Optional[date] = None
    target_completion: Optional[date] = None
    inspecting_officer: str
    next_inspection: Optional[date] = None
    inspection_type: Optional[str] = None
    inspections_completed: List[Dict[str, Any]] = []
    fees_paid: bool = False
    fee_amount: Optional[float] = None
    structural_calculations: bool = False
    energy_assessment: bool = False
    accessibility_compliance: bool = False
    fire_safety_compliance: bool = False

# ============================================================================
# LAND CHARGES (Enhanced)
# ============================================================================

class LandChargesSearchType(str, Enum):
    LLC1 = "LLC1 - Full Search"
    CON29 = "CON29 - Standard Enquiries"
    CON29O = "CON29O - Optional Enquiries"
    PERSONAL_SEARCH = "Personal Search"

class LandChargesStatus(str, Enum):
    RECEIVED = "Received"
    PROCESSING = "Processing"
    QUERIES_RAISED = "Queries Raised"
    COMPLETED = "Completed"
    DISPATCHED = "Dispatched"
    CANCELLED = "Cancelled"

class LandChargesSearch(BaseModel):
    id: str = Field(..., description="Land charges search reference")
    search_type: LandChargesSearchType
    status: LandChargesStatus
    property_address: str
    applicant_name: str
    applicant_address: str
    solicitor_firm: Optional[str] = None
    solicitor_contact: Optional[str] = None
    date_received: date
    date_completed: Optional[date] = None
    processing_officer: str
    fee_paid: bool = False
    fee_amount: float
    urgent_search: bool = False
    charges_found: List[str] = []
    planning_applications: List[str] = []
    building_control_approvals: List[str] = []
    tree_preservation_orders: List[str] = []
    conservation_area_designation: bool = False
    listed_building_designation: bool = False
    environmental_designations: List[str] = []

# ============================================================================
# WASTE REGULATORY SERVICES (New)
# ============================================================================

class WasteLicenceType(str, Enum):
    WASTE_CARRIERS = "Waste Carrier Licence"
    WASTE_TRANSFER = "Waste Transfer Note"
    SCRAP_METAL = "Scrap Metal Dealer"
    WASTE_EXEMPTION = "Waste Exemption"
    HAZARDOUS_WASTE = "Hazardous Waste Consignment"

class WasteComplianceStatus(str, Enum):
    COMPLIANT = "Compliant"
    MINOR_BREACH = "Minor Breach"
    MAJOR_BREACH = "Major Breach"
    ENFORCEMENT_ACTION = "Enforcement Action"
    SUSPENDED = "Licence Suspended"
    REVOKED = "Licence Revoked"

class WasteRegulatoryCase(BaseModel):
    id: str = Field(..., description="Waste regulatory case reference")
    licence_type: WasteLicenceType
    status: WasteComplianceStatus
    business_name: str
    business_address: str
    license_holder: str
    contact_details: str
    licence_number: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    renewal_date: Optional[date] = None
    annual_fee_due: Optional[float] = None
    last_inspection: Optional[date] = None
    next_inspection: Optional[date] = None
    inspecting_officer: str
    compliance_history: List[Dict[str, Any]] = []
    enforcement_actions: List[Dict[str, Any]] = []
    waste_types: List[str] = []
    annual_tonnage: Optional[float] = None
    environmental_permit_required: bool = False
    site_visit_required: bool = False

# ============================================================================
# PRIVATE SECTOR HOUSING (New)
# ============================================================================

class HousingEnforcementType(str, Enum):
    HMO_LICENCE = "HMO Licence"
    SELECTIVE_LICENCE = "Selective Licensing"
    HOUSING_STANDARDS = "Housing Standards Inspection"
    CATEGORY_1_HAZARD = "Category 1 Hazard"
    CATEGORY_2_HAZARD = "Category 2 Hazard"
    IMPROVEMENT_NOTICE = "Improvement Notice"
    PROHIBITION_ORDER = "Prohibition Order"
    EMERGENCY_WORKS = "Emergency Remedial Action"

class HousingComplianceStatus(str, Enum):
    COMPLIANT = "Compliant"
    MINOR_ISSUES = "Minor Issues Identified"
    SERIOUS_HAZARDS = "Serious Hazards Found"
    ENFORCEMENT_ACTION = "Enforcement Action Required"
    WORKS_IN_PROGRESS = "Remedial Works in Progress"
    PROHIBITED = "Property Prohibited"

class PrivateHousingCase(BaseModel):
    id: str = Field(..., description="Private housing case reference")
    enforcement_type: HousingEnforcementType
    status: HousingComplianceStatus
    property_address: str
    property_type: str = Field(..., description="House/Flat/HMO/etc")
    landlord_name: str
    landlord_contact: str
    managing_agent: Optional[str] = None
    tenant_contact: Optional[str] = None
    date_reported: date
    inspection_date: Optional[date] = None
    inspecting_officer: str
    hazards_identified: List[Dict[str, Any]] = []
    hhsrs_score: Optional[int] = None  # Housing Health & Safety Rating System
    licence_required: bool = False
    licence_number: Optional[str] = None
    licence_expiry: Optional[date] = None
    enforcement_notices: List[Dict[str, Any]] = []
    works_completion_date: Optional[date] = None
    follow_up_inspection: Optional[date] = None
    prosecution_considered: bool = False
    civil_penalty_issued: Optional[float] = None

# ============================================================================
# INTEGRATED CASE MANAGEMENT
# ============================================================================

class CaseType(str, Enum):
    PLANNING = "Planning Application"
    BUILDING_CONTROL = "Building Control"
    LAND_CHARGES = "Land Charges Search"
    WASTE_REGULATORY = "Waste Regulatory"
    PRIVATE_HOUSING = "Private Sector Housing"

class CasePriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"

class IntegratedRegulatoryCase(BaseModel):
    """Master case that can link multiple regulatory services"""
    id: str = Field(..., description="Master case reference")
    case_type: CaseType
    priority: CasePriority
    property_address: str
    primary_contact: str
    contact_details: str
    description: str
    date_created: datetime
    last_updated: datetime
    assigned_officer: str
    department: str
    related_cases: List[str] = []  # Links to other case types for same property
    status_summary: str
    target_resolution: Optional[date] = None
    public_facing: bool = True  # Whether visible in public portal
    internal_notes: List[str] = []
    document_references: List[str] = []
    gis_reference: Optional[str] = None
    ward: str
    parish: Optional[str] = None

# ============================================================================
# USER MANAGEMENT & PERMISSIONS
# ============================================================================

class UserRole(str, Enum):
    SUPER_ADMIN = "Super Administrator"
    DEPT_MANAGER = "Department Manager"
    SENIOR_OFFICER = "Senior Officer"
    CASE_OFFICER = "Case Officer"
    ADMIN_SUPPORT = "Administrative Support"
    EXTERNAL_CONSULTEE = "External Consultee"
    PUBLIC_USER = "Public User"

class Department(str, Enum):
    PLANNING = "Planning & Transportation"
    BUILDING_CONTROL = "Building Control"
    ENVIRONMENTAL_HEALTH = "Environmental Health"
    HOUSING = "Housing Services"
    LEGAL = "Legal Services"
    FINANCE = "Finance"
    CUSTOMER_SERVICES = "Customer Services"

class UserPermissions(BaseModel):
    user_id: str
    role: UserRole
    department: Department
    can_view_cases: List[CaseType]
    can_edit_cases: List[CaseType]
    can_approve_cases: List[CaseType]
    can_assign_cases: bool = False
    can_access_reports: bool = False
    can_manage_users: bool = False
    can_configure_system: bool = False
    geographical_restrictions: Optional[List[str]] = None  # Ward/parish restrictions
    
# ============================================================================
# AUDIT TRAIL
# ============================================================================

class AuditAction(str, Enum):
    CREATED = "Created"
    VIEWED = "Viewed"
    UPDATED = "Updated"
    DELETED = "Deleted"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    ASSIGNED = "Assigned"
    COMMENTED = "Commented"
    DOCUMENT_UPLOADED = "Document Uploaded"
    DOCUMENT_DOWNLOADED = "Document Downloaded"

class AuditEntry(BaseModel):
    id: str
    case_id: str
    case_type: CaseType
    action: AuditAction
    user_id: str
    user_name: str
    timestamp: datetime
    ip_address: str
    changes_made: Optional[Dict[str, Any]] = None
    previous_values: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    foi_sensitive: bool = False  # Flag for FOI disclosure considerations