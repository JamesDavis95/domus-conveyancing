"""
Production Database Models for Domus Planning Platform
Real database schema with proper relationships and constraints
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    plan_type = Column(String(50), default="core")  # core, professional, enterprise
    subscription_status = Column(String(50), default="trial")  # trial, active, cancelled, past_due
    stripe_customer_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    projects = relationship("Project", back_populates="organization")
    documents = relationship("Document", back_populates="organization")
    subscriptions = relationship("Subscription", back_populates="organization")
    payments = relationship("Payment", back_populates="organization")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # developer, consultant, landowner, admin
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    created_projects = relationship("Project", back_populates="creator")
    created_documents = relationship("Document", back_populates="creator")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    proposed_use = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="draft")  # draft, analyzing, analyzed, submitted, approved, refused
    approval_probability = Column(Float, nullable=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="projects")
    creator = relationship("User", back_populates="created_projects")
    documents = relationship("Document", back_populates="project")
    analyses = relationship("Planning_Analysis", back_populates="project")
    properties = relationship("Property", back_populates="project")

class Planning_Analysis(Base):
    __tablename__ = "planning_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    approval_probability = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    key_constraints = Column(JSON, nullable=True)  # List of constraint names
    recommendations = Column(JSON, nullable=True)  # List of recommendations
    rationale = Column(Text, nullable=True)
    model_version = Column(String(50), default="v1.0")
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="analyses")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    document_type = Column(String(100), nullable=False)  # planning_statement, design_access, heritage, etc.
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    word_count = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    file_path = Column(String(500), nullable=True)  # S3 path for generated files
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="documents")
    organization = relationship("Organization", back_populates="documents")
    creator = relationship("User", back_populates="created_documents")

class Property(Base):
    __tablename__ = "properties"
    
    id = Column(Integer, primary_key=True, index=True)
    address = Column(Text, nullable=False)
    uprn = Column(String(50), nullable=True, index=True)
    postcode = Column(String(20), nullable=True, index=True)
    
    # Land Registry Data
    title_number = Column(String(50), nullable=True)
    tenure = Column(String(50), nullable=True)
    last_sale_price = Column(Integer, nullable=True)
    last_sale_date = Column(DateTime, nullable=True)
    
    # EPC Data
    epc_rating = Column(String(10), nullable=True)
    energy_score = Column(Integer, nullable=True)
    potential_rating = Column(String(10), nullable=True)
    
    # Planning Data
    council_tax_band = Column(String(10), nullable=True)
    flood_risk = Column(String(100), nullable=True)
    conservation_area = Column(Boolean, default=False)
    listed_building = Column(Boolean, default=False)
    
    # Relationships
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    project = relationship("Project", back_populates="properties")
    created_at = Column(DateTime, default=datetime.utcnow)

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    stripe_subscription_id = Column(String(255), unique=True, nullable=False)
    plan_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)  # active, cancelled, past_due
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="subscriptions")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    stripe_invoice_id = Column(String(255), unique=True, nullable=False)
    amount = Column(Integer, nullable=False)  # Amount in pence
    currency = Column(String(10), default="gbp")
    status = Column(String(50), nullable=False)  # succeeded, failed, pending
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="payments")

class Usage(Base):
    __tablename__ = "usage"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resource_type = Column(String(100), nullable=False)  # site_analyses, documents, api_calls
    resource_id = Column(Integer, nullable=True)  # ID of the resource created
    created_at = Column(DateTime, default=datetime.utcnow)

class Offset_Listing(Base):
    __tablename__ = "offset_listings"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    listing_type = Column(String(50), nullable=False)  # supply, demand
    
    # Location
    location = Column(String(500), nullable=False)
    postcode = Column(String(20), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Biodiversity Details
    habitat_type = Column(String(100), nullable=False)  # grassland, woodland, wetland
    distinctiveness = Column(String(50), nullable=False)  # low, medium, high
    units_available = Column(Float, nullable=False)
    units_required = Column(Float, nullable=True)  # For demand listings
    
    # Pricing
    price_per_unit = Column(Integer, nullable=True)  # Pence per unit
    budget_per_unit = Column(Integer, nullable=True)  # For demand listings
    total_value = Column(Integer, nullable=True)
    
    # Timeline
    available_from = Column(DateTime, nullable=True)
    required_by = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(50), default="active")  # active, matched, completed, cancelled
    
    # Verification
    baseline_survey_complete = Column(Boolean, default=False)
    planning_permission = Column(Boolean, default=False)
    defra_approved = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Offset_Contract(Base):
    __tablename__ = "offset_contracts"
    
    id = Column(Integer, primary_key=True, index=True)
    supply_listing_id = Column(Integer, ForeignKey("offset_listings.id"), nullable=False)
    demand_listing_id = Column(Integer, ForeignKey("offset_listings.id"), nullable=False)
    
    # Contract Details
    units = Column(Float, nullable=False)
    price_per_unit = Column(Integer, nullable=False)  # Pence per unit
    total_amount = Column(Integer, nullable=False)  # Pence
    
    # Status
    status = Column(String(50), default="draft")  # draft, signed, payment_pending, completed, cancelled
    
    # Payment
    escrow_amount = Column(Integer, nullable=True)  # Amount held in escrow
    payment_schedule = Column(JSON, nullable=True)  # Payment milestones
    
    # Timeline
    delivery_date = Column(DateTime, nullable=True)
    monitoring_years = Column(Integer, default=30)
    
    # Signatures
    supplier_signed_at = Column(DateTime, nullable=True)
    buyer_signed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class API_Key(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    rate_limit_per_hour = Column(Integer, default=1000)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

class Audit_Log(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    action = Column(String(255), nullable=False)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database configuration
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Database URL - use environment variable in production
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./domus_production.db")

# For PostgreSQL in production, use:
# DATABASE_URL = "postgresql://user:password@localhost/domus_production"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
    echo=False           # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)