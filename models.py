"""
Clean SQLAlchemy models for Domus conveyancing system
No demo data or seed content - production ready
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, DECIMAL, JSON
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
    assigned_cases = relationship("Case", back_populates="assigned_user", foreign_keys="Case.assigned_to")
    client_cases = relationship("Case", back_populates="client_user", foreign_keys="Case.client_user_id")
    uploaded_documents = relationship("Document", back_populates="uploader")
    audit_actions = relationship("AuditLog", back_populates="actor")

class Organization(Base):
    __tablename__ = "orgs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="owned_orgs", foreign_keys=[owner_user_id])
    memberships = relationship("Membership", back_populates="organization")
    cases = relationship("Case", back_populates="organization")
    documents = relationship("Document", back_populates="organization")
    subscriptions = relationship("Subscription", back_populates="organization")
    invoices = relationship("Invoice", back_populates="organization")
    api_keys = relationship("ApiKey", back_populates="organization")
    audit_logs = relationship("AuditLog", back_populates="organization")

class Membership(Base):
    __tablename__ = "memberships"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    role = Column(String, nullable=False)  # Owner, Admin, Manager, Staff, BillingOnly, ReadOnly, Client
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="memberships", foreign_keys=[user_id])
    organization = relationship("Organization", back_populates="memberships")
    inviter = relationship("User", foreign_keys=[invited_by])

class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False)  # planning, submitted, approved, rejected
    property_address = Column(Text, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    client_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="cases")
    assigned_user = relationship("User", back_populates="assigned_cases", foreign_keys=[assigned_to])
    client_user = relationship("User", back_populates="client_cases", foreign_keys=[client_user_id])
    events = relationship("CaseEvent", back_populates="case")
    documents = relationship("Document", back_populates="case")

class CaseEvent(Base):
    __tablename__ = "case_events"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    type = Column(String, nullable=False)  # created, updated, assigned, status_change, etc.
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    case = relationship("Case", back_populates="events")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    filename = Column(String, nullable=False)
    storage_key = Column(String, nullable=False)  # S3 key or file path
    mime_type = Column(String, nullable=True)
    size = Column(Integer, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="documents")
    case = relationship("Case", back_populates="documents")
    uploader = relationship("User", back_populates="uploaded_documents")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    plan = Column(String, nullable=True)  # developer, devpro, consultant, enterprise
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
    amount = Column(DECIMAL, nullable=True)
    status = Column(String, nullable=True)
    hosted_invoice_url = Column(String, nullable=True)
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
    target_type = Column(String, nullable=True)  # user, case, document, billing, etc.
    target_id = Column(String, nullable=True)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="audit_logs")
    actor = relationship("User", back_populates="audit_actions")