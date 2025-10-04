from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, Float, Enum, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(enum.Enum):
    DEVELOPER = "developer"
    CONSULTANT = "consultant"
    LANDOWNER = "landowner"
    AUTHORITY = "authority"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class PlanType(enum.Enum):
    CORE = "core"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"

class ProjectStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class ContractStatus(enum.Enum):
    DRAFT = "draft"
    SIGNED = "signed"
    PAYMENT_PENDING = "payment_pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# CORE PLATFORM MODELS

class Orgs(Base):
    __tablename__ = "orgs"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    plan = Column(Enum(PlanType), default=PlanType.CORE)
    billing_customer_id = Column(String(255), nullable=True)  # Stripe customer ID
    training_opt_in = Column(Boolean, default=False)  # AI training consent
    white_label_config = Column(JSON, nullable=True)  # Enterprise branding
    api_rate_limit = Column(Integer, default=1000)  # Requests per hour
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    users = relationship("Users", back_populates="org")
    projects = relationship("Projects", back_populates="org")
    marketplace_supply = relationship("MarketplaceSupply", back_populates="org")
    marketplace_demand = relationship("MarketplaceDemand", back_populates="org")
    contracts = relationship("Contracts", back_populates="org")

class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    plan = Column(Enum(PlanType), default=PlanType.CORE)
    plan_expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    org = relationship("Orgs", back_populates="users")

class Projects(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    title = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    site_geometry = Column(JSON, nullable=True)  # GeoJSON
    lpa_code = Column(String(10), nullable=True)  # Local Planning Authority
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT)
    ai_score = Column(Float, nullable=True)  # Approval probability 0-100
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    org = relationship("Orgs", back_populates="projects")
    documents = relationship("Documents", back_populates="project")
    bundles = relationship("Bundles", back_populates="project")
    analysis_snapshots = relationship("AnalysisSnapshots", back_populates="project")

# PLANNING AI ANALYSIS & SNAPSHOTS

class AnalysisSnapshots(Base):
    __tablename__ = "analysis_snapshots"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    analysis_type = Column(String(50), nullable=False)  # full, objection_risk, appeals
    score = Column(Float, nullable=True)  # 0-100 approval probability
    analysis_json = Column(JSON, nullable=False)  # Full analysis data
    citations_json = Column(JSON, nullable=False)  # Policy citations & precedents
    confidence = Column(Float, nullable=True)  # 0-1 confidence score
    model_version = Column(String(50), nullable=False)  # AI model version
    lpa_context_json = Column(JSON, nullable=True)  # HDT/5YHLS/tilted balance
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Projects", back_populates="analysis_snapshots")
    org = relationship("Orgs")

class Documents(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    type = Column(String(100), nullable=False)  # 'planning_statement', 'heritage_assessment', etc.
    version = Column(Integer, default=1)
    storage_url = Column(String(500), nullable=False)  # S3 URL
    size = Column(Integer, nullable=True)  # File size in bytes
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Projects", back_populates="documents")

class Bundles(Base):
    __tablename__ = "bundles"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    storage_url = Column(String(500), nullable=False)  # ZIP file S3 URL
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Projects", back_populates="bundles")

# MARKETPLACE MODELS

class MarketplaceSupply(Base):
    __tablename__ = "marketplace_supply"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    location = Column(String(255), nullable=False)
    units_available = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    status = Column(String(50), default="active")
    kyc_account_id = Column(String(255), nullable=True)  # Stripe Connect account
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    org = relationship("Orgs", back_populates="marketplace_supply")

class MarketplaceDemand(Base):
    __tablename__ = "marketplace_demand"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    region = Column(String(255), nullable=False)
    units_required = Column(Integer, nullable=False)
    budget = Column(Float, nullable=False)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    org = relationship("Orgs", back_populates="marketplace_demand")

class Contracts(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    supply_id = Column(Integer, ForeignKey("marketplace_supply.id"), nullable=False)
    demand_id = Column(Integer, ForeignKey("marketplace_demand.id"), nullable=False)
    status = Column(Enum(ContractStatus), default=ContractStatus.DRAFT)
    payment_intent_id = Column(String(255), nullable=True)  # Stripe Payment Intent
    audit_json = Column(JSON, nullable=True)  # Full audit trail
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    org = relationship("Orgs", back_populates="contracts")
    supply = relationship("MarketplaceSupply")
    demand = relationship("MarketplaceDemand")

# USAGE & QUOTAS

class UsageCounters(Base):
    __tablename__ = "usage_counters"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    month = Column(String(7), nullable=False)  # Format: "2024-10"
    projects_used = Column(Integer, default=0)
    docs_used = Column(Integer, default=0)
    api_calls_used = Column(Integer, default=0)
    viability_runs_used = Column(Integer, default=0)
    bng_calculations_used = Column(Integer, default=0)
    transport_assessments_used = Column(Integer, default=0)
    environment_assessments_used = Column(Integer, default=0)
    submission_packs_used = Column(Integer, default=0)
    
    # Relationships
    org = relationship("Orgs")

# VIABILITY ASSESSMENT MODULE

class ViabilityPresets(Base):
    __tablename__ = "viability_presets"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    config_json = Column(JSON, nullable=False)  # All viability parameters
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    org = relationship("Orgs")
    runs = relationship("ViabilityRuns", back_populates="preset")

class ViabilityRuns(Base):
    __tablename__ = "viability_runs"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    preset_id = Column(Integer, ForeignKey("viability_presets.id"), nullable=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    inputs_json = Column(JSON, nullable=False)  # All input parameters
    outputs_json = Column(JSON, nullable=False)  # GDV, costs, residual, profit
    scenario_name = Column(String(255), nullable=True)
    storage_url = Column(String(500), nullable=True)  # S3 URL for exports
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Projects")
    preset = relationship("ViabilityPresets", back_populates="runs")
    org = relationship("Orgs")

# BIODIVERSITY NET GAIN (BNG) MODULE

class BNGBaselines(Base):
    __tablename__ = "bng_baselines"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    baseline_data_json = Column(JSON, nullable=False)  # Habitat metrics
    storage_url = Column(String(500), nullable=True)  # S3 URL for uploads
    sha256_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Projects")
    org = relationship("Orgs")
    calculations = relationship("BNGCalculations", back_populates="baseline")

class BNGCalculations(Base):
    __tablename__ = "bng_calculations"
    id = Column(Integer, primary_key=True)
    baseline_id = Column(Integer, ForeignKey("bng_baselines.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    scheme_data_json = Column(JSON, nullable=False)  # Proposed scheme
    calculation_json = Column(JSON, nullable=False)  # Units, deficit/surplus
    net_gain_percentage = Column(Float, nullable=True)
    deficit_units = Column(Float, nullable=True)
    surplus_units = Column(Float, nullable=True)
    storage_url = Column(String(500), nullable=True)  # S3 URL for statements
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    baseline = relationship("BNGBaselines", back_populates="calculations")
    project = relationship("Projects")
    org = relationship("Orgs")

# TRANSPORT & HIGHWAYS MODULE

class TransportInputs(Base):
    __tablename__ = "transport_inputs"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    development_type = Column(String(100), nullable=False)
    units_or_floorspace = Column(Float, nullable=False)
    trip_rates_json = Column(JSON, nullable=False)
    parking_requirements_json = Column(JSON, nullable=False)
    access_assumptions_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Projects")
    org = relationship("Orgs")
    assessments = relationship("TransportAssessments", back_populates="inputs")

class TransportAssessments(Base):
    __tablename__ = "transport_assessments"
    id = Column(Integer, primary_key=True)
    inputs_id = Column(Integer, ForeignKey("transport_inputs.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    assessment_json = Column(JSON, nullable=False)  # Trip generation, impacts
    risk_score = Column(Float, nullable=True)  # 0-100
    mitigations_json = Column(JSON, nullable=False)  # Recommended mitigations
    storage_url = Column(String(500), nullable=True)  # S3 URL for statements
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    inputs = relationship("TransportInputs", back_populates="assessments")
    project = relationship("Projects")
    org = relationship("Orgs")

# ENVIRONMENT & CLIMATE MODULE

class EnvironmentRisks(Base):
    __tablename__ = "environment_risks"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    assessment_type = Column(String(100), nullable=False)  # air_quality, climate, etc
    risk_data_json = Column(JSON, nullable=False)  # Environmental indicators
    risk_score = Column(Float, nullable=True)  # 0-100
    mitigations_json = Column(JSON, nullable=False)  # Recommended mitigations
    citations_json = Column(JSON, nullable=False)  # Policy citations
    storage_url = Column(String(500), nullable=True)  # S3 URL for statements
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Projects")
    org = relationship("Orgs")

# SUBMISSION PACK MODULE

class SubmissionPacks(Base):
    __tablename__ = "submission_packs"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    pack_name = Column(String(255), nullable=False)
    contents_json = Column(JSON, nullable=False)  # List of included documents
    manifest_json = Column(JSON, nullable=False)  # SHA256 checksums
    storage_url = Column(String(500), nullable=False)  # S3 URL for ZIP
    sha256_hash = Column(String(64), nullable=False)
    authority_token = Column(String(255), nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Projects")
    org = relationship("Orgs")

# OBJECTION RISK & APPEALS MODULE

class ObjectionCorpus(Base):
    __tablename__ = "objection_corpus"
    id = Column(Integer, primary_key=True)
    lpa_code = Column(String(10), nullable=False, index=True)
    application_ref = Column(String(50), nullable=True)
    theme = Column(String(100), nullable=False)  # traffic, design, etc
    objection_text = Column(Text, nullable=False)
    url = Column(String(500), nullable=True)
    date_submitted = Column(DateTime, nullable=True)
    embedding_vector = Column(JSON, nullable=True)  # For semantic search
    created_at = Column(DateTime, default=datetime.utcnow)

class AppealsCases(Base):
    __tablename__ = "appeals_cases"
    id = Column(Integer, primary_key=True)
    lpa_code = Column(String(10), nullable=False, index=True)
    appeal_ref = Column(String(50), nullable=False, unique=True)
    application_ref = Column(String(50), nullable=True)
    decision = Column(String(20), nullable=False)  # allowed, dismissed
    appeal_type = Column(String(50), nullable=False)  # householder, etc
    development_type = Column(String(100), nullable=True)
    reasons_json = Column(JSON, nullable=False)  # Reasons for decision
    inspector_report_url = Column(String(500), nullable=True)
    decision_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# LPA METRICS & ANALYTICS

class LPAMetrics(Base):
    __tablename__ = "lpa_metrics"
    lpa_code = Column(String(10), primary_key=True)
    lpa_name = Column(String(255), nullable=False)
    decision_times_json = Column(JSON, nullable=False)  # Average times by type
    approval_rate = Column(Float, nullable=True)  # 0-100
    appeal_success_rate = Column(Float, nullable=True)  # 0-100
    housing_delivery_test = Column(Float, nullable=True)
    five_year_land_supply = Column(Float, nullable=True)
    tilted_balance = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ORG INSIGHTS & KNOWLEDGE GRAPH

class OrgGraphNodes(Base):
    __tablename__ = "org_graph_nodes"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    node_type = Column(String(50), nullable=False)  # risk, mitigation, success_factor
    label = Column(String(255), nullable=False)
    properties_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    org = relationship("Orgs")
    project = relationship("Projects")

class OrgGraphEdges(Base):
    __tablename__ = "org_graph_edges"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    from_node_id = Column(Integer, ForeignKey("org_graph_nodes.id"), nullable=False)
    to_node_id = Column(Integer, ForeignKey("org_graph_nodes.id"), nullable=False)
    edge_type = Column(String(50), nullable=False)  # causes, mitigates, relates_to
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    org = relationship("Orgs")
    from_node = relationship("OrgGraphNodes", foreign_keys=[from_node_id])
    to_node = relationship("OrgGraphNodes", foreign_keys=[to_node_id])

# COLLABORATION MODULE

class Collaborators(Base):
    __tablename__ = "collaborators"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # viewer, contributor, manager
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    invited_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="pending")  # pending, active, revoked
    
    # Relationships
    project = relationship("Projects")
    org = relationship("Orgs")
    inviter = relationship("Users")

class Comments(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for authority
    author_email = Column(String(255), nullable=True)  # For external users
    context = Column(Enum(enum.Enum('CommentContext', 'doc analysis authority')), nullable=False)
    body = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)  # Mentions, attachments, etc
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Projects")
    author = relationship("Users")

# AUDIT & COMPLIANCE

class AuditLogs(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)  # view, generate, comment, etc
    resource_type = Column(String(50), nullable=False)  # project, document, etc
    resource_id = Column(String(50), nullable=False)
    metadata_json = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    org = relationship("Orgs")
    user = relationship("Users")

# ENTERPRISE FEATURES

class ApiKeys(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    key_hash = Column(String(255), nullable=False, index=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    org = relationship("Orgs")

# AUTHORITY PORTAL

class AuthorityTokens(Base):
    __tablename__ = "authority_tokens"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    
    # Relationships
    project = relationship("Projects")

# LEGACY MODELS (keeping for backward compatibility)

class Matters(Base):
    __tablename__ = "matters"
    id = Column(Integer, primary_key=True)
    ref = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="created")

    files = relationship("Files", back_populates="matter", cascade="all, delete-orphan")
    findings = relationship("Findings", back_populates="matter", cascade="all, delete-orphan")
    risks = relationship("Risks", back_populates="matter", cascade="all, delete-orphan")

class Files(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    kind = Column(String, nullable=True, default="search")
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    ocr_applied = Column(Boolean, default=False)

    matter = relationship("Matters", back_populates="files")

class Findings(Base):
    __tablename__ = "findings"
    id = Column(Integer, primary_key=True)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(Text, nullable=False)
    confidence = Column(Integer, default=1)

    matter = relationship("Matters", back_populates="findings")

class Risks(Base):
    __tablename__ = "risks"
    id = Column(Integer, primary_key=True)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    code = Column(String, nullable=False)
    level = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    matter = relationship("Matters", back_populates="risks")

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    plan_type = Column(Enum(PlanType), default=PlanType.CORE)
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    stripe_customer_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    trial_end = Column(DateTime, nullable=True)
    
    users = relationship("User", back_populates="organization")
    subscriptions = relationship("Subscription", back_populates="organization")
    payments = relationship("Payment", back_populates="organization")
    usage_records = relationship("Usage", back_populates="organization")

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    stripe_subscription_id = Column(String, unique=True, nullable=False)
    plan_type = Column(Enum(PlanType), nullable=False)
    status = Column(String, nullable=False)
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)
    
    organization = relationship("Organization", back_populates="subscriptions")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    stripe_invoice_id = Column(String, unique=True, nullable=False)
    amount = Column(Integer, nullable=False)  # Amount in pence
    currency = Column(String, default="gbp")
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="payments")

class Usage(Base):
    __tablename__ = "usage"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resource_type = Column(String, nullable=False)  # site_analyses, documents, api_calls
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="usage_records")
    user = relationship("User", back_populates="usage_records")

# MONITORING AND FRESHNESS MODELS

class SourceFreshness(Base):
    __tablename__ = "source_freshness"
    id = Column(Integer, primary_key=True)
    source = Column(String(255), nullable=False, unique=True)  # e.g., 'policy_corpus', 'lpa_metrics'
    last_updated_at = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False)  # 'updated', 'failed', 'in_progress'

# Database Configuration - Production Ready
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

# Get database URL from environment (PostgreSQL for production, SQLite for local)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./production.db")

# Handle PostgreSQL URLs (Render provides postgres://, but SQLAlchemy needs postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with appropriate configuration
if DATABASE_URL.startswith("postgresql://"):
    # PostgreSQL configuration for production
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False  # Set to True for debugging
    )
else:
    # SQLite configuration for local development
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
