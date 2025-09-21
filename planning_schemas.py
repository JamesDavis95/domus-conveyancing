from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Keep existing Evidence model - it's useful across all services
class Evidence(BaseModel):
    file_id: str
    page: Optional[int] = None
    note: Optional[str] = None

# ==================== PLANNING APPLICATION MODELS ====================

class ApplicationType(str, Enum):
    FULL = "Full Planning Permission"
    OUTLINE = "Outline Planning Permission"
    RESERVED = "Reserved Matters"
    HOUSEHOLDER = "Householder Application"
    CHANGE_OF_USE = "Change of Use"
    LISTED_BUILDING = "Listed Building Consent"
    ADVERTISEMENT = "Advertisement Consent"
    TREE_WORK = "Tree Work Application"
    PRIOR_NOTIFICATION = "Prior Notification"

class ApplicationStatus(str, Enum):
    RECEIVED = "Received"
    VALIDATED = "Validated"
    UNDER_CONSIDERATION = "Under Consideration"
    CONSULTATION = "Public Consultation"
    COMMITTEE = "Planning Committee"
    APPROVED = "Approved"
    REFUSED = "Refused"
    WITHDRAWN = "Withdrawn"
    APPEALED = "Appealed"

class PolicyCompliance(BaseModel):
    policy_reference: str  # "LP1", "NPPF Para 11", etc.
    policy_title: str
    compliance_status: str  # "Compliant", "Non-Compliant", "Requires Assessment"
    evidence: str
    confidence_score: float
    officer_review_required: bool
    ai_analysis: Optional[str] = None

class PlanningApplication(BaseModel):
    application_ref: str  # "24/00123/FUL"
    application_type: ApplicationType
    property_address: str
    uprn: Optional[str] = None
    description: str
    received_date: datetime
    target_date: datetime
    status: ApplicationStatus
    
    # Applicant information
    applicant_name: str
    applicant_address: str
    applicant_email: Optional[str] = None
    agent_name: Optional[str] = None
    agent_contact: Optional[str] = None
    
    # Planning details
    case_officer: Optional[str] = None
    ward: Optional[str] = None
    parish: Optional[str] = None
    site_area: Optional[float] = None
    
    # AI Analysis results
    policy_assessments: List[PolicyCompliance] = []
    risk_score: Optional[float] = None
    recommendation: Optional[str] = None
    
    # Documents and evidence
    documents: List[Evidence] = []
    consultation_responses: List[str] = []

# ==================== LAND CHARGES MODELS ====================

class Charge(BaseModel):
    charge_type: str
    present: bool
    reference: Optional[str] = None
    source: Optional[str] = None
    evidence: Optional[Evidence] = None
    date_registered: Optional[datetime] = None
    affecting_area: Optional[str] = None

class LLC1(BaseModel):
    charges: List[Charge] = []
    search_date: datetime
    local_authority: str
    property_description: str

# ==================== INTEGRATED PLATFORM MODELS ====================

class IntegratedCase(BaseModel):
    """
    Master case model that can link across all services
    This represents the integrated platform approach councils want
    """
    case_id: str
    property_address: str
    uprn: Optional[str] = None
    
    # Related applications across services
    planning_applications: List[PlanningApplication] = []
    land_charges: Optional[LLC1] = None
    
    # Cross-service analytics
    compliance_overview: dict = {}
    timeline: List[dict] = []
    risk_assessment: dict = {}

# Keep existing models for backward compatibility
class PlanningDecision(BaseModel):
    ref: str
    date: Optional[str] = None
    description: Optional[str] = None
    decision: Optional[str] = None
    evidence: Optional[Evidence] = None

class RoadsFootways(BaseModel):
    abutting_highway_adopted: Optional[bool] = None
    authority: Optional[str] = None
    evidence: Optional[Evidence] = None

class Con29(BaseModel):
    planning_decisions: List[PlanningDecision] = []
    roads_footways: Optional[RoadsFootways] = None
    enforcement_notices_present: Optional[bool] = None
    contaminated_land_designation: Optional[bool] = None
    s106_present: Optional[bool] = None
    cil_outstanding: Optional[bool] = None
    flood_zone: Optional[str] = None
    radon_affected: Optional[bool] = None
    building_regs_completion_present: Optional[bool] = None