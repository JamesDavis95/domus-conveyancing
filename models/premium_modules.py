"""
Database Models for Premium Modules
Creates tables: viability_runs, scheme_variants, policy_updates, chat_sessions, submissions
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any

Base = declarative_base()

class ViabilityRun(Base):
    """Development viability calculation results"""
    __tablename__ = "viability_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Input parameters
    site_area = Column(Float, nullable=False)
    development_type = Column(String(50), nullable=False)  # residential, commercial, mixed
    units_proposed = Column(Integer, nullable=True)
    gross_floor_area = Column(Float, nullable=True)
    
    # Financial inputs
    land_value = Column(Float, nullable=False)
    build_costs_per_sqm = Column(Float, nullable=False)
    sales_values_per_sqm = Column(Float, nullable=False)
    professional_fees_percent = Column(Float, default=12.0)
    contingency_percent = Column(Float, default=5.0)
    finance_rate_percent = Column(Float, default=6.0)
    developer_profit_percent = Column(Float, default=20.0)
    
    # Calculated results
    gross_development_value = Column(Float, nullable=True)
    total_costs = Column(Float, nullable=True)
    developer_profit = Column(Float, nullable=True)
    residual_land_value = Column(Float, nullable=True)
    internal_rate_return = Column(Float, nullable=True)
    viability_status = Column(String(20), nullable=True)  # viable, marginal, unviable
    
    # Metadata
    calculation_parameters = Column(JSON, nullable=True)  # Full calculation breakdown
    sensitivity_analysis = Column(JSON, nullable=True)    # Risk scenarios
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SchemeVariant(Base):
    """AI-generated development scheme variants"""
    __tablename__ = "scheme_variants"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    viability_run_id = Column(Integer, ForeignKey("viability_runs.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Variant details
    variant_name = Column(String(100), nullable=False)
    variant_description = Column(Text, nullable=True)
    
    # Planning parameters
    units_residential = Column(Integer, default=0)
    units_commercial = Column(Integer, default=0)
    building_height_stories = Column(Integer, nullable=True)
    density_units_per_hectare = Column(Float, nullable=True)
    parking_spaces = Column(Integer, nullable=True)
    affordable_housing_percent = Column(Float, nullable=True)
    
    # Scoring
    planning_score = Column(Float, nullable=True)      # 0-100 planning compliance
    profit_score = Column(Float, nullable=True)       # 0-100 financial return
    combined_score = Column(Float, nullable=True)     # planning_score × profit_score
    
    # Design constraints
    constraints_met = Column(JSON, nullable=True)     # Which constraints satisfied
    policy_compliance = Column(JSON, nullable=True)   # NPPF/Local policy compliance
    risk_factors = Column(JSON, nullable=True)        # Identified risks
    
    # AI generation metadata
    generation_model = Column(String(50), default="gpt-4")
    generation_prompt = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Status
    status = Column(String(20), default="generated")  # generated, selected, implemented
    is_preferred = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PolicyUpdate(Base):
    """Legislation and policy change tracking"""
    __tablename__ = "policy_updates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Policy identification
    policy_type = Column(String(50), nullable=False)  # NPPF, NPPG, local_plan, spd
    policy_source = Column(String(100), nullable=False)  # gov.uk, council name
    policy_title = Column(String(200), nullable=False)
    policy_reference = Column(String(100), nullable=True)  # Section/paragraph
    
    # Change details
    change_type = Column(String(50), nullable=False)  # new, amended, revoked
    change_summary = Column(Text, nullable=False)
    change_detail = Column(Text, nullable=True)
    effective_date = Column(DateTime, nullable=True)
    
    # Impact analysis
    affected_sectors = Column(JSON, nullable=True)    # residential, commercial, etc.
    impact_level = Column(String(20), nullable=True)  # critical, major, minor
    impact_description = Column(Text, nullable=True)
    
    # Monitoring
    source_url = Column(String(500), nullable=True)
    last_checked = Column(DateTime, default=datetime.utcnow)
    check_frequency_days = Column(Integer, default=7)
    
    # Alerts
    alert_sent = Column(Boolean, default=False)
    alert_sent_at = Column(DateTime, nullable=True)
    affected_projects_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ChatSession(Base):
    """Planning Copilot chat sessions"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Session metadata
    session_title = Column(String(200), nullable=True)
    session_type = Column(String(50), default="general")  # general, project_specific, policy_query
    context_data = Column(JSON, nullable=True)  # Project data, documents, etc.
    
    # AI configuration
    model_version = Column(String(50), default="gpt-4")
    system_prompt = Column(Text, nullable=True)
    temperature = Column(Float, default=0.7)
    
    # Session status
    status = Column(String(20), default="active")  # active, completed, archived
    message_count = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)

class ChatMessage(Base):
    """Individual messages in Planning Copilot sessions"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    
    # Message content
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # AI response metadata (for assistant messages)
    model_used = Column(String(50), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Citations and sources (for assistant messages)
    citations = Column(JSON, nullable=True)  # Referenced documents, policies
    sources = Column(JSON, nullable=True)    # NPPF sections, precedents
    
    # Message metadata
    message_index = Column(Integer, nullable=False)  # Order in conversation
    is_hidden = Column(Boolean, default=False)       # For system messages
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    session = relationship("ChatSession", back_populates="messages")

# Add back-reference
ChatSession.messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class Submission(Base):
    """Planning application submissions to councils"""
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Submission details
    submission_type = Column(String(50), nullable=False)  # full_application, outline, etc.
    council_id = Column(String(100), nullable=False)     # Target council
    council_reference = Column(String(100), nullable=True)  # Council's ref number
    
    # Submission package
    submission_pack_id = Column(String(100), nullable=True)  # Internal pack ID
    authority_token = Column(String(100), nullable=True)     # Access token for council
    document_manifest = Column(JSON, nullable=True)          # List of documents + checksums
    total_documents = Column(Integer, default=0)
    total_size_mb = Column(Float, default=0.0)
    
    # Submission tracking
    status = Column(String(50), default="draft")  # draft, submitted, acknowledged, etc.
    submission_method = Column(String(20), nullable=True)  # email, api, manual
    submitted_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    
    # Council processing
    validation_status = Column(String(20), nullable=True)  # valid, invalid, pending
    target_decision_date = Column(DateTime, nullable=True)
    actual_decision_date = Column(DateTime, nullable=True)
    decision_outcome = Column(String(50), nullable=True)   # approved, refused, withdrawn
    
    # Communication log
    email_thread = Column(JSON, nullable=True)  # Email exchanges
    status_updates = Column(JSON, nullable=True)  # Timeline of status changes
    
    # Metadata
    submission_notes = Column(Text, nullable=True)
    fees_paid = Column(Float, nullable=True)
    fee_reference = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Migration script for Alembic
def create_premium_module_tables():
    """
    Creates all premium module tables
    Run this with: alembic revision --autogenerate -m "Add premium module tables"
    """
    pass  # Alembic will auto-generate the migration