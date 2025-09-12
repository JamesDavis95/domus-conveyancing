# 🏛️ **ENTERPRISE MODELS FOR COUNCIL PROCUREMENT**
# Complete data model for multi-tenant council platform

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, Float, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from enum import Enum
import uuid

Base = declarative_base()

# ==================== ORGANIZATION & USER MANAGEMENT ====================

class UserRole(Enum):
    SUPER_ADMIN = "super_admin"           # Platform admin
    COUNCIL_ADMIN = "council_admin"       # Council IT admin
    DEPARTMENT_HEAD = "department_head"   # Department manager
    SENIOR_OFFICER = "senior_officer"     # Team lead
    OFFICER = "officer"                   # Regular user
    READ_ONLY = "read_only"              # View only access

class Department(Enum):
    PLANNING = "planning"
    HOUSING = "housing" 
    LEGAL = "legal"
    FINANCE = "finance"
    ENVIRONMENTAL_HEALTH = "environmental_health"
    BUILDING_CONTROL = "building_control"
    HIGHWAYS = "highways"
    LICENSING = "licensing"

class Organization(Base):
    """Council/Local Authority"""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)  # "East Hertfordshire District Council"
    short_name = Column(String(50), nullable=False)  # "EHDC"
    type = Column(String(50), nullable=False)  # "District Council", "County Council", etc.
    
    # Contact details
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(255))
    website = Column(String(255))
    
    # Billing & subscription
    subscription_tier = Column(String(50), default="standard")  # standard, premium, enterprise
    monthly_fee = Column(Float, default=0)
    per_search_cost = Column(Float, default=25.00)
    
    # Configuration
    settings = Column(JSON)  # Custom council settings
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    matters = relationship("Matter", back_populates="organization")
    invoices = relationship("Invoice", back_populates="organization")

class User(Base):
    """Council staff member"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Identity
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    job_title = Column(String(100))
    
    # Access control
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.OFFICER)
    department = Column(SQLEnum(Department), nullable=False)
    permissions = Column(JSON)  # Specific permissions
    
    # Authentication
    hashed_password = Column(String(255))
    is_sso_user = Column(Boolean, default=False)  # Uses council SSO
    last_login = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    matters_assigned = relationship("Matter", back_populates="assigned_officer")
    audit_logs = relationship("AuditLog", back_populates="user")

# ==================== CASE/MATTER MANAGEMENT ====================

class MatterStatus(Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    IN_PROGRESS = "in_progress" 
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"

class MatterPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class Matter(Base):
    """Search case/matter"""
    __tablename__ = "matters"
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    assigned_officer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Matter details
    ref = Column(String(50), unique=True, index=True)  # Auto-generated reference
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Property details
    property_address = Column(Text, nullable=False)
    postcode = Column(String(10), nullable=False)
    uprn = Column(String(20))
    title_number = Column(String(20))
    
    # Workflow
    status = Column(SQLEnum(MatterStatus), default=MatterStatus.DRAFT)
    priority = Column(SQLEnum(MatterPriority), default=MatterPriority.NORMAL)
    department = Column(SQLEnum(Department), nullable=False)
    
    # Timing
    requested_date = Column(DateTime, default=datetime.utcnow)
    target_completion_date = Column(DateTime)
    completed_date = Column(DateTime)
    
    # Financial
    estimated_cost = Column(Float)
    actual_cost = Column(Float)
    billing_code = Column(String(50))  # For charge-back
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="matters")
    assigned_officer = relationship("User", back_populates="matters_assigned")
    files = relationship("File", back_populates="matter")
    findings = relationship("Finding", back_populates="matter")
    risks = relationship("Risk", back_populates="matter")
    workflow_steps = relationship("WorkflowStep", back_populates="matter")

class File(Base):
    """Uploaded documents"""
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    
    # File details
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # Processing
    file_type = Column(String(50))  # "search_pdf", "planning_doc", "site_plan", etc.
    processing_status = Column(String(50), default="pending")
    ocr_applied = Column(Boolean, default=False)
    ai_processed = Column(Boolean, default=False)
    
    # Security
    checksum = Column(String(64))  # SHA256 for integrity
    is_sensitive = Column(Boolean, default=False)
    retention_date = Column(DateTime)  # When to delete per GDPR
    
    # Metadata
    uploaded_by_id = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    matter = relationship("Matter", back_populates="files")

# ==================== WORKFLOW MANAGEMENT ====================

class WorkflowStepType(Enum):
    UPLOAD_DOCUMENTS = "upload_documents"
    SUPERVISOR_REVIEW = "supervisor_review"
    QUALITY_CHECK = "quality_check"
    CUSTOMER_APPROVAL = "customer_approval"
    FINAL_SIGN_OFF = "final_sign_off"

class WorkflowStepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    REJECTED = "rejected"

class WorkflowStep(Base):
    """Individual workflow step"""
    __tablename__ = "workflow_steps"
    
    id = Column(Integer, primary_key=True)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Step details
    step_type = Column(SQLEnum(WorkflowStepType), nullable=False)
    step_name = Column(String(255), nullable=False)
    step_order = Column(Integer, nullable=False)
    
    # Status
    status = Column(SQLEnum(WorkflowStepStatus), default=WorkflowStepStatus.PENDING)
    due_date = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Results
    outcome = Column(String(50))  # "approved", "rejected", etc.
    comments = Column(Text)
    
    # Relationships
    matter = relationship("Matter", back_populates="workflow_steps")

# ==================== FINANCIAL MANAGEMENT ====================

class InvoiceStatus(Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class Invoice(Base):
    """Billing/invoicing"""
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Invoice details
    invoice_number = Column(String(50), unique=True, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Amounts
    subtotal = Column(Float, nullable=False)
    vat_amount = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    
    # Status
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    issued_date = Column(DateTime)
    due_date = Column(DateTime)
    paid_date = Column(DateTime)
    
    # Relationships
    organization = relationship("Organization", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice")

class InvoiceLineItem(Base):
    """Individual charges on invoice"""
    __tablename__ = "invoice_line_items"
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=True)
    
    # Item details
    description = Column(String(255), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    # Metadata
    billing_code = Column(String(50))
    department = Column(SQLEnum(Department))
    
    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")

# ==================== FINDINGS & RISKS ====================

class Finding(Base):
    """Extracted data from searches"""
    __tablename__ = "findings"
    
    id = Column(Integer, primary_key=True)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    
    # Finding details
    category = Column(String(100), nullable=False)  # "planning", "environmental", etc.
    key = Column(String(255), nullable=False)
    value = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    
    # Source
    source_file_id = Column(Integer, ForeignKey("files.id"), nullable=True)
    page_number = Column(Integer)
    
    # Verification
    is_verified = Column(Boolean, default=False)
    verified_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime)
    
    # Relationships
    matter = relationship("Matter", back_populates="findings")

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Risk(Base):
    """Identified risks"""
    __tablename__ = "risks"
    
    id = Column(Integer, primary_key=True)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    
    # Risk details
    risk_code = Column(String(20), nullable=False)  # "ENV001", "PLAN004", etc.
    risk_type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Assessment
    level = Column(SQLEnum(RiskLevel), nullable=False)
    probability = Column(Float)  # 0.0 to 1.0
    impact_score = Column(Integer)  # 1-10
    
    # Actions
    mitigation_required = Column(Boolean, default=False)
    mitigation_notes = Column(Text)
    
    # Relationships
    matter = relationship("Matter", back_populates="risks")

# ==================== AUDIT & COMPLIANCE ====================

class AuditEventType(Enum):
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    MATTER_CREATED = "matter_created"
    MATTER_UPDATED = "matter_updated"
    FILE_UPLOADED = "file_uploaded"
    FILE_DOWNLOADED = "file_downloaded"
    DATA_EXPORTED = "data_exported"
    PERMISSION_CHANGED = "permission_changed"

class AuditLog(Base):
    """Complete audit trail"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Event details
    event_type = Column(SQLEnum(AuditEventType), nullable=False)
    resource_type = Column(String(50))  # "matter", "file", "user", etc.
    resource_id = Column(String(50))
    action = Column(String(100))
    
    # Context
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    session_id = Column(String(100))
    
    # Changes
    old_values = Column(JSON)
    new_values = Column(JSON)
    
    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")

# ==================== SYSTEM CONFIGURATION ====================

class SystemSetting(Base):
    """System-wide configuration"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    data_type = Column(String(20), default="string")  # string, integer, boolean, json
    description = Column(Text)
    is_sensitive = Column(Boolean, default=False)  # Hide from UI
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Integration(Base):
    """External system integrations"""
    __tablename__ = "integrations"
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    # Integration details
    name = Column(String(100), nullable=False)
    integration_type = Column(String(50), nullable=False)  # "crm", "finance", "document_store"
    provider = Column(String(100))  # "Capita", "Civica", "Northgate"
    
    # Configuration
    config = Column(JSON)  # Connection details, API keys, etc.
    is_active = Column(Boolean, default=True)
    
    # Status
    last_sync = Column(DateTime)
    sync_status = Column(String(50))
    error_message = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)