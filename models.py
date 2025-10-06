"""
SQLAlchemy models for Domus AI Planning Platform
AI-powered development intelligence and planning analysis
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, DECIMAL, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database_config import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    owned_orgs = relationship("Organization", back_populates="owner", foreign_keys="Organization.owner_user_id")
    memberships = relationship("Membership", back_populates="user")
    created_sites = relationship("Site", back_populates="created_by_user", foreign_keys="Site.created_by")
    analyses = relationship("Analysis", back_populates="created_by_user")
    ai_chats = relationship("AiChat", back_populates="user")
    documents = relationship("Document", back_populates="created_by_user")
    audit_actions = relationship("AuditLog", back_populates="actor")

class Organization(Base):
    __tablename__ = "orgs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    plan_slug = Column(String, nullable=True)  # developer, developer_pro, consultant, enterprise
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="owned_orgs", foreign_keys=[owner_user_id])
    memberships = relationship("Membership", back_populates="organization")
    sites = relationship("Site", back_populates="organization")
    credit_wallets = relationship("CreditWallet", back_populates="organization")
    documents = relationship("Document", back_populates="organization")
    submission_bundles = relationship("SubmissionBundle", back_populates="organization")
    subscriptions = relationship("Subscription", back_populates="organization")
    invoices = relationship("Invoice", back_populates="organization")
    api_keys = relationship("ApiKey", back_populates="organization")
    audit_logs = relationship("AuditLog", back_populates="organization")

class Membership(Base):
    __tablename__ = "memberships"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    org_id = Column(Integer, ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)  # Owner, Admin, Manager, Staff, BillingOnly, ReadOnly, Client, LA
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="memberships")
    organization = relationship("Organization", back_populates="memberships")

class Site(Base):
    __tablename__ = "sites"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    postcode = Column(String, nullable=True)
    coordinates = Column(JSON, nullable=True)  # [lat, lon]
    boundary_geojson = Column(JSON, nullable=True)
    site_area = Column(Float, nullable=True)
    existing_use = Column(String, nullable=True)
    development_type = Column(String, nullable=True)  # RESIDENTIAL, COMMERCIAL, MIXED_USE
    proposal_description = Column(Text, nullable=True)
    dwelling_count = Column(Integer, nullable=True)
    status = Column(String, default="ACTIVE", nullable=False)  # ACTIVE, ARCHIVED
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="sites")
    created_by_user = relationship("User", back_populates="created_sites", foreign_keys=[created_by])
    site_files = relationship("SiteFile", back_populates="site")
    analyses = relationship("Analysis", back_populates="site")
    ai_chats = relationship("AiChat", back_populates="site")
    documents = relationship("Document", back_populates="site")
    submission_bundles = relationship("SubmissionBundle", back_populates="site")

class SiteFile(Base):
    __tablename__ = "site_files"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    kind = Column(String, nullable=False)  # boundary, title, flood, constraints
    filename = Column(String, nullable=False)
    s3_url = Column(String, nullable=False)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    site = relationship("Site", back_populates="site_files")

class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    summary_html = Column(Text, nullable=True)
    suggestions_json = Column(JSON, nullable=True)
    approval_probability = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    model_tag = Column(String, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    site = relationship("Site", back_populates="analyses")
    created_by_user = relationship("User", back_populates="analyses")

class AiChat(Base):
    __tablename__ = "ai_chats"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    messages_json = Column(JSON, nullable=False)  # Array of {role, content, timestamp}
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    site = relationship("Site", back_populates="ai_chats")
    user = relationship("User", back_populates="ai_chats")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=True)
    type = Column(String, nullable=False)  # planning_statement, design_access, heritage_note, transport_note
    title = Column(String, nullable=False)
    html_draft = Column(Text, nullable=True)
    pdf_url = Column(String, nullable=True)
    status = Column(String, default="DRAFT", nullable=False)  # DRAFT, GENERATED, FINALIZED
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="documents")
    site = relationship("Site", back_populates="documents")
    created_by_user = relationship("User", back_populates="documents")

class SubmissionBundle(Base):
    __tablename__ = "submission_bundles"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    zip_url = Column(String, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="submission_bundles")
    site = relationship("Site", back_populates="submission_bundles")

class CreditWallet(Base):
    __tablename__ = "credit_wallets"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    credit_type = Column(String, nullable=False)  # ai_analysis, document, submission
    balance = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="credit_wallets")
    ledger_entries = relationship("CreditLedger", back_populates="wallet")

class CreditLedger(Base):
    __tablename__ = "credit_ledger"
    
    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("credit_wallets.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    credit_type = Column(String, nullable=False)
    delta = Column(Integer, nullable=False)  # positive for add, negative for consume
    reason = Column(String, nullable=False)
    ref_id = Column(String, nullable=True)  # reference to analysis, document, bundle
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    wallet = relationship("CreditWallet", back_populates="ledger_entries")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    plan_slug = Column(String, nullable=True)  # developer, developer_pro, consultant, enterprise
    status = Column(String, nullable=True)  # active, canceled, past_due, etc.
    current_period_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="subscriptions")

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    stripe_invoice_id = Column(String, nullable=True)
    amount_gbp = Column(DECIMAL, nullable=True)
    status = Column(String, nullable=True)
    hosted_invoice_url = Column(String, nullable=True)
    raw_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="invoices")

class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    name = Column(String, nullable=False)
    hashed_key = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="api_keys")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    entity = Column(String, nullable=True)  # site, analysis, document, billing, user, etc.
    entity_id = Column(String, nullable=True)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="audit_logs")
    actor = relationship("User", back_populates="audit_actions")

class PlanLimit(Base):
    __tablename__ = "plan_limits"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_slug = Column(String, nullable=False, index=True)
    key = Column(String, nullable=False)  # max_sites, ai_chat_enabled, calculator_enabled
    value = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)