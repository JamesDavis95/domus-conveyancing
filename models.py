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
    
    # Relationships
    org = relationship("Orgs")

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
