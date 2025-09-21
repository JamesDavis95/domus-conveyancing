"""
Security, Compliance & User Management System
RM6259 Framework Compliant | GDPR Compliant | Government Security Standards
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
import hashlib
import secrets
import jwt

# ============================================================================
# USER MANAGEMENT & AUTHENTICATION
# ============================================================================

class UserRole(str, Enum):
    SUPER_ADMIN = "Super Administrator"
    COUNCIL_ADMIN = "Council Administrator"  
    DEPT_MANAGER = "Department Manager"
    SENIOR_OFFICER = "Senior Officer"
    PLANNING_OFFICER = "Planning Officer"
    BUILDING_CONTROL_OFFICER = "Building Control Officer"
    ENVIRONMENTAL_HEALTH_OFFICER = "Environmental Health Officer"
    HOUSING_OFFICER = "Housing Standards Officer"
    LAND_CHARGES_OFFICER = "Land Charges Officer"
    CASE_OFFICER = "Case Officer"
    ADMIN_SUPPORT = "Administrative Support"
    EXTERNAL_CONSULTEE = "External Consultee"
    PUBLIC_USER = "Public User"
    COUNCILLOR = "Elected Member"
    LEGAL_OFFICER = "Legal Officer"

class Department(str, Enum):
    PLANNING = "Planning & Development"
    BUILDING_CONTROL = "Building Control"
    ENVIRONMENTAL_HEALTH = "Environmental Health"
    HOUSING = "Housing Services"
    LEGAL = "Legal & Democratic Services"
    FINANCE = "Finance & Resources"
    CUSTOMER_SERVICES = "Customer Services"
    CHIEF_EXECUTIVE = "Chief Executive"
    ECONOMY_ENVIRONMENT = "Economy & Environment"
    COMMUNITY_WELLBEING = "Community Wellbeing"

class SecurityClearanceLevel(str, Enum):
    PUBLIC = "Public"
    OFFICIAL = "Official"
    OFFICIAL_SENSITIVE = "Official-Sensitive"
    SECRET = "Secret"  # Rare in councils
    TOP_SECRET = "Top Secret"  # Very rare

class User(BaseModel):
    id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., description="Email address")
    full_name: str = Field(..., description="Full name")
    role: UserRole
    department: Department
    security_clearance: SecurityClearanceLevel = SecurityClearanceLevel.OFFICIAL
    is_active: bool = True
    is_verified: bool = False
    created_date: datetime
    last_login: Optional[datetime] = None
    password_hash: str = Field(..., description="Bcrypt hashed password")
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    session_timeout: int = Field(default=3600, description="Session timeout in seconds")
    failed_login_attempts: int = 0
    account_locked_until: Optional[datetime] = None
    
    # GDPR Compliance
    data_processing_consent: bool = True
    marketing_consent: bool = False
    data_retention_date: Optional[datetime] = None
    
    # Government Security
    background_check_date: Optional[datetime] = None
    security_training_date: Optional[datetime] = None
    need_to_know_areas: List[str] = []

class UserPermissions(BaseModel):
    user_id: str
    # Service Access
    can_access_planning: bool = False
    can_access_building_control: bool = False
    can_access_land_charges: bool = False
    can_access_waste_regulatory: bool = False
    can_access_housing: bool = False
    
    # Action Permissions
    can_view_cases: bool = True
    can_create_cases: bool = False
    can_edit_cases: bool = False
    can_delete_cases: bool = False
    can_approve_cases: bool = False
    can_reject_cases: bool = False
    
    # Administrative Permissions
    can_assign_cases: bool = False
    can_manage_users: bool = False
    can_configure_system: bool = False
    can_access_audit_logs: bool = False
    can_export_data: bool = False
    can_generate_reports: bool = False
    
    # Geographic Restrictions
    ward_restrictions: Optional[List[str]] = None
    parish_restrictions: Optional[List[str]] = None
    postcode_restrictions: Optional[List[str]] = None
    
    # Data Classification Access
    can_access_personal_data: bool = False
    can_access_sensitive_data: bool = False
    can_access_commercial_data: bool = False

# ============================================================================
# RM6259 FRAMEWORK COMPLIANCE
# ============================================================================

class RM6259Lot(str, Enum):
    LOT_1 = "Lot 1: Technology Products"
    LOT_2 = "Lot 2: Technology Services" 
    LOT_3 = "Lot 3: Technology Consultancy"

class RM6259Compliance(BaseModel):
    """Crown Commercial Service RM6259 Vehicle & Asset Solutions Framework Compliance"""
    
    framework_reference: str = "RM6259"
    framework_name: str = "Vehicle & Asset Solutions"
    applicable_lots: List[RM6259Lot] = [RM6259Lot.LOT_3]  # Technology Consultancy
    
    # Supplier Requirements
    supplier_registered: bool = True
    duns_number: Optional[str] = "123456789"  # D-U-N-S number
    companies_house_number: Optional[str] = "12345678"
    vat_registration: Optional[str] = "GB123456789"
    
    # Technical Standards
    iso_27001_certified: bool = True
    iso_9001_certified: bool = True
    cyber_essentials_plus: bool = True
    government_security_classifications: List[SecurityClearanceLevel] = [
        SecurityClearanceLevel.PUBLIC,
        SecurityClearanceLevel.OFFICIAL,
        SecurityClearanceLevel.OFFICIAL_SENSITIVE
    ]
    
    # Service Delivery
    uk_delivery_capability: bool = True
    sme_subcontracting_commitment: float = 25.0  # % commitment to SME subcontracting
    social_value_policy: bool = True
    environmental_policy: bool = True
    
    # Financial Requirements
    minimum_insurance_cover: float = 2000000.0  # £2M
    financial_threshold_met: bool = True
    credit_rating: str = "Stable"

class GDPRCompliance(BaseModel):
    """GDPR and Data Protection Compliance"""
    
    # Legal Basis for Processing
    legal_basis_public_task: bool = True  # Article 6(1)(e)
    legal_basis_legitimate_interest: bool = True  # Article 6(1)(f)
    
    # Data Subject Rights
    right_of_access_implemented: bool = True
    right_to_rectification_implemented: bool = True
    right_to_erasure_implemented: bool = True
    right_to_portability_implemented: bool = True
    right_to_object_implemented: bool = True
    
    # Technical and Organisational Measures
    data_encryption_at_rest: bool = True
    data_encryption_in_transit: bool = True
    access_logging_enabled: bool = True
    data_backup_procedures: bool = True
    incident_response_procedures: bool = True
    
    # Governance
    data_protection_officer_appointed: bool = True
    privacy_impact_assessments_conducted: bool = True
    data_retention_policy_defined: bool = True
    third_party_processor_agreements: bool = True
    
    # Breach Notification
    breach_detection_capability: bool = True
    seventy_two_hour_notification_procedure: bool = True

class GovernmentSecurityStandards(BaseModel):
    """UK Government Security Standards Compliance"""
    
    # Security Policy Framework
    spf_compliant: bool = True
    security_governance_framework: bool = True
    
    # Personnel Security
    baseline_personnel_security_standard: bool = True
    security_clearance_processes: bool = True
    ongoing_personnel_security: bool = True
    
    # Physical and Environmental Security
    physical_security_controls: bool = True
    environmental_controls: bool = True
    secure_disposal_procedures: bool = True
    
    # Information Security
    information_classification_scheme: bool = True
    access_control_procedures: bool = True
    cryptographic_controls: bool = True
    
    # Incident Management
    incident_response_capability: bool = True
    forensic_readiness: bool = True
    business_continuity_planning: bool = True

# ============================================================================
# AUDIT TRAIL & COMPLIANCE LOGGING
# ============================================================================

class AuditEventType(str, Enum):
    # User Actions
    LOGIN = "User Login"
    LOGOUT = "User Logout"
    LOGIN_FAILED = "Failed Login Attempt"
    PASSWORD_CHANGED = "Password Changed"
    ACCOUNT_LOCKED = "Account Locked"
    
    # Case Management
    CASE_CREATED = "Case Created"
    CASE_VIEWED = "Case Viewed"
    CASE_UPDATED = "Case Updated"
    CASE_DELETED = "Case Deleted"
    CASE_ASSIGNED = "Case Assigned"
    CASE_APPROVED = "Case Approved"
    CASE_REJECTED = "Case Rejected"
    
    # Document Management
    DOCUMENT_UPLOADED = "Document Uploaded"
    DOCUMENT_VIEWED = "Document Viewed"
    DOCUMENT_DOWNLOADED = "Document Downloaded"
    DOCUMENT_DELETED = "Document Deleted"
    
    # System Administration
    USER_CREATED = "User Created"
    USER_MODIFIED = "User Modified"
    USER_DELETED = "User Deleted"
    PERMISSIONS_CHANGED = "Permissions Changed"
    SYSTEM_CONFIG_CHANGED = "System Configuration Changed"
    
    # Data Protection
    DATA_EXPORT = "Data Export"
    DATA_IMPORT = "Data Import"
    PERSONAL_DATA_ACCESSED = "Personal Data Accessed"
    GDPR_REQUEST_RECEIVED = "GDPR Subject Request Received"
    GDPR_REQUEST_PROCESSED = "GDPR Subject Request Processed"
    
    # Security Events
    SECURITY_BREACH = "Security Breach Detected"
    SUSPICIOUS_ACTIVITY = "Suspicious Activity Detected"
    PRIVILEGE_ESCALATION = "Privilege Escalation Attempt"

class ComplianceAuditEntry(BaseModel):
    id: str = Field(..., description="Unique audit entry ID")
    timestamp: datetime
    event_type: AuditEventType
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: str
    user_agent: Optional[str] = None
    
    # Event Details
    resource_type: Optional[str] = None  # case, document, user, etc.
    resource_id: Optional[str] = None
    action_description: str
    
    # Data Changes
    previous_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    
    # Security Context
    security_classification: SecurityClearanceLevel = SecurityClearanceLevel.OFFICIAL
    data_subject_id: Optional[str] = None  # For GDPR compliance
    
    # Compliance Flags
    foi_sensitive: bool = False  # Freedom of Information sensitivity
    personal_data_involved: bool = False
    requires_dpn_notification: bool = False  # Data Protection Notice
    
    # Legal Hold
    legal_hold_flag: bool = False
    retention_date: Optional[datetime] = None

# ============================================================================
# SOCIAL VALUE FRAMEWORK
# ============================================================================

class SocialValueArea(str, Enum):
    EMPLOYMENT = "Employment & Skills"
    COMMUNITY = "Community Development"
    ENVIRONMENT = "Environmental Impact"
    INNOVATION = "Innovation & Technology"
    EQUALITY = "Equality & Diversity"
    SUPPLY_CHAIN = "Supply Chain Development"

class SocialValueMeasure(BaseModel):
    area: SocialValueArea
    metric_name: str
    target_value: float
    actual_value: float
    measurement_unit: str
    reporting_period: str
    evidence_provided: bool = False
    
class SocialValueCompliance(BaseModel):
    """Social Value Act 2012 Compliance for Public Procurement"""
    
    # Employment & Skills (30% weighting typically)
    local_employment_created: int = 0
    apprenticeships_created: int = 0
    training_opportunities: int = 0
    work_experience_placements: int = 0
    
    # Community Development (25% weighting typically)
    community_initiatives_supported: int = 0
    voluntary_sector_partnerships: int = 0
    local_spend_percentage: float = 0.0
    
    # Environmental Impact (25% weighting typically)
    carbon_reduction_percentage: float = 0.0
    waste_reduction_percentage: float = 0.0
    renewable_energy_usage: float = 0.0
    
    # Innovation (20% weighting typically)
    innovation_initiatives: int = 0
    technology_transfer: int = 0
    research_partnerships: int = 0
    
    # Overall Scoring
    social_value_measures: List[SocialValueMeasure] = []
    total_social_value_score: float = 0.0
    reporting_frequency: str = "Quarterly"

# ============================================================================
# ACCESSIBILITY COMPLIANCE
# ============================================================================

class AccessibilityStandard(str, Enum):
    WCAG_2_1_A = "WCAG 2.1 Level A"
    WCAG_2_1_AA = "WCAG 2.1 Level AA"
    WCAG_2_1_AAA = "WCAG 2.1 Level AAA"
    EN_301_549 = "EN 301 549 (European Standard)"
    SECTION_508 = "Section 508 (US Federal)"

class AccessibilityCompliance(BaseModel):
    """Web Content Accessibility Guidelines (WCAG) 2.1 AA Compliance"""
    
    target_standard: AccessibilityStandard = AccessibilityStandard.WCAG_2_1_AA
    compliance_level_achieved: AccessibilityStandard = AccessibilityStandard.WCAG_2_1_AA
    
    # Principle 1: Perceivable
    text_alternatives_provided: bool = True
    captions_provided: bool = True
    content_distinguishable: bool = True
    
    # Principle 2: Operable  
    keyboard_accessible: bool = True
    no_seizure_content: bool = True
    navigable_interface: bool = True
    
    # Principle 3: Understandable
    readable_text: bool = True
    predictable_functionality: bool = True
    input_assistance: bool = True
    
    # Principle 4: Robust
    compatible_with_assistive_tech: bool = True
    
    # Testing & Validation
    automated_testing_conducted: bool = True
    manual_testing_conducted: bool = True
    user_testing_with_disabilities: bool = True
    
    # Accessibility Statement
    accessibility_statement_published: bool = True
    feedback_mechanism_provided: bool = True
    
    # Regular Reviews
    last_audit_date: Optional[datetime] = None
    next_audit_due: Optional[datetime] = None

# ============================================================================
# INTEGRATION CAPABILITIES
# ============================================================================

class IntegrationStandard(str, Enum):
    REST_API = "REST API"
    SOAP_WS = "SOAP Web Service"  
    GRAPHQL = "GraphQL"
    WEBHOOK = "Webhook"
    FILE_TRANSFER = "File Transfer (SFTP/FTP)"
    DATABASE_SYNC = "Database Synchronization"
    MESSAGE_QUEUE = "Message Queue"

class ExternalSystemType(str, Enum):
    GIS_MAPPING = "GIS/Mapping System"
    FINANCE_SYSTEM = "Finance System"
    HR_SYSTEM = "HR System"
    CRM_SYSTEM = "CRM System"
    DOCUMENT_MANAGEMENT = "Document Management"
    EMAIL_SYSTEM = "Email System"
    PAYMENT_GATEWAY = "Payment Gateway"
    NATIONAL_DATABASE = "National Database"
    GOV_UK_NOTIFY = "GOV.UK Notify"
    GOV_UK_PAY = "GOV.UK Pay"

class IntegrationCapability(BaseModel):
    system_name: str
    system_type: ExternalSystemType
    integration_methods: List[IntegrationStandard]
    data_formats_supported: List[str] = ["JSON", "XML", "CSV"]
    authentication_methods: List[str] = ["API Key", "OAuth 2.0", "SAML", "JWT"]
    encryption_supported: bool = True
    real_time_sync: bool = True
    batch_processing: bool = True
    error_handling: bool = True
    monitoring_alerts: bool = True
