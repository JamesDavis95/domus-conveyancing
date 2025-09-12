import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db import Base  # reuse your existing Base from db.py

def _id():
    return str(uuid.uuid4())

class LAMatter(Base):
    __tablename__ = "la_matters"
    id = Column(String, primary_key=True, default=_id)
    ref = Column(String, nullable=False, unique=True)
    address = Column(String, nullable=True)
    uprn = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Applicant details
    applicant_name = Column(String, nullable=True)
    applicant_email = Column(String, nullable=True)
    applicant_phone = Column(String, nullable=True)
    applicant_address = Column(Text, nullable=True)
    
    # Product requests
    llc1_requested = Column(String, nullable=False, default="false")  # true|false
    con29_requested = Column(String, nullable=False, default="true")  # true|false  
    con29o_requested = Column(String, nullable=False, default="false") # true|false
    additional_enquiries = Column(Text, nullable=True)  # JSON array
    
    # Payment & fees
    fee_calculated = Column(Float, nullable=True)
    payment_status = Column(String, nullable=False, default="pending")  # pending|paid|failed|refunded
    payment_reference = Column(String, nullable=True)
    payment_method = Column(String, nullable=True)  # card|bacs|exemption
    exemption_reason = Column(String, nullable=True)
    
    # SLA Management  
    sla_due_date = Column(DateTime, nullable=True)
    sla_status = Column(String, nullable=False, default="on_time")  # on_time|at_risk|overdue
    priority = Column(String, nullable=False, default="standard")  # urgent|priority|standard
    
    # Workflow & assignment
    assigned_to = Column(String, nullable=True)  # User ID
    assigned_team = Column(String, nullable=True) 
    
    # Status flow timestamps
    received_at = Column(DateTime, nullable=True)
    first_scan_at = Column(DateTime, nullable=True)
    in_progress_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True) 
    qa_started_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    issued_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="created")  # created|received|assigned|in_progress|processed|qa_review|approved|issued
    
    # NEW: Spatial fields (nullable - preserves existing data)
    geometry_wkt = Column(Text, nullable=True)             # Property boundary as WKT
    centroid_wkt = Column(Text, nullable=True)             # Center point as WKT  
    easting = Column(Integer, nullable=True)               # OS grid reference
    northing = Column(Integer, nullable=True)
    latitude = Column(Float, nullable=True)                # WGS84 coordinates
    longitude = Column(Float, nullable=True)
    council_boundary_wkt = Column(Text, nullable=True)     # Council area as WKT
    
    orders = relationship("LAOrder", back_populates="matter", cascade="all, delete-orphan")
    findings = relationship("LAFinding", back_populates="matter", cascade="all, delete-orphan")
    risks = relationship("LARisk", back_populates="matter", cascade="all, delete-orphan")
    files = relationship("LAFile", back_populates="matter", cascade="all, delete-orphan")
    spatial_layers = relationship("LASpatialLayer", back_populates="matter", cascade="all, delete-orphan")

class LAOrder(Base):
    __tablename__ = "la_orders"
    id = Column(String, primary_key=True, default=_id)
    matter_id = Column(String, ForeignKey("la_matters.id"), nullable=False)
    council_code = Column(String, nullable=False)
    types = Column(String, nullable=False)  # "LLC1,CON29"
    provider_ref = Column(String, nullable=True)
    status = Column(String, nullable=False, default="SUBMITTED")  # SUBMITTED|PENDING|READY|FAILED
    created_at = Column(DateTime, server_default=func.now())

    matter = relationship("LAMatter", back_populates="orders")
    documents = relationship("LADocument", back_populates="order", cascade="all, delete-orphan")

class LADocument(Base):
    __tablename__ = "la_documents"
    id = Column(String, primary_key=True, default=_id)
    order_id = Column(String, ForeignKey("la_orders.id"), nullable=False)
    kind = Column(String, nullable=False)  # LLC1|CON29|CON29O
    file_path = Column(String, nullable=False)
    content_type = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    order = relationship("LAOrder", back_populates="documents")

class LAFile(Base):
    __tablename__ = "la_files"
    id = Column(String, primary_key=True, default=_id)
    matter_id = Column(String, ForeignKey("la_matters.id"), nullable=False)
    filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    kind = Column(String, nullable=False, default="search")  # search|supporting|other
    content_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime, nullable=True)
    processing_status = Column(String, nullable=False, default="pending")  # pending|processing|completed|failed

    matter = relationship("LAMatter", back_populates="files")

class LAFinding(Base):
    __tablename__ = "la_findings"
    id = Column(String, primary_key=True, default=_id)
    matter_id = Column(String, ForeignKey("la_matters.id"), nullable=False)
    key = Column(String, nullable=False)    # e.g. "con29.roads_footways.abutting_highway_adopted"
    value = Column(Text, nullable=True)     # JSON string
    evidence_file = Column(String, nullable=True)
    evidence_page = Column(Integer, nullable=True)
    confidence = Column(Integer, nullable=True)  # 0..100
    created_at = Column(DateTime, server_default=func.now())

    matter = relationship("LAMatter", back_populates="findings")

class LARisk(Base):
    __tablename__ = "la_risks"
    id = Column(String, primary_key=True, default=_id)
    matter_id = Column(String, ForeignKey("la_matters.id"), nullable=False)
    code = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # LOW|MEDIUM|HIGH
    message = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)     # JSON array string
    created_at = Column(DateTime, server_default=func.now())

    matter = relationship("LAMatter", back_populates="risks")

# NEW: Spatial intelligence models for GIS foundation
class LASpatialLayer(Base):
    """Spatial overlays for automated CON29 answering"""
    __tablename__ = "la_spatial_layers"
    id = Column(String, primary_key=True, default=_id)
    matter_id = Column(String, ForeignKey("la_matters.id"), nullable=False)
    layer_type = Column(String, nullable=False)  # flood_zone|conservation_area|tpo|planning|highways
    source = Column(String, nullable=False)      # OS|EA|council|manual
    geometry_wkt = Column(Text, nullable=False)  # Geometry as WKT string
    properties = Column(Text, nullable=True)     # JSON properties
    confidence = Column(Float, default=1.0)     # Confidence score 0-1
    created_at = Column(DateTime, server_default=func.now())
    
    matter = relationship("LAMatter", back_populates="spatial_layers")

class LAAutomatedAnswer(Base):
    """Automated CON29 answers from spatial analysis"""
    __tablename__ = "la_automated_answers"
    id = Column(String, primary_key=True, default=_id)
    matter_id = Column(String, ForeignKey("la_matters.id"), nullable=False)
    question_code = Column(String, nullable=False)  # CON29 question code
    question_text = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    method = Column(String, nullable=False)      # spatial_overlay|api_lookup|manual
    confidence = Column(Float, default=1.0)
    spatial_evidence = Column(Text, nullable=True)  # JSON spatial evidence
    created_at = Column(DateTime, server_default=func.now())
    
    matter = relationship("LAMatter")

# NEW: Phase 2A Models - Payment, SLA, QA, Communications

class LAPayment(Base):
    """Payment tracking for LA matters"""
    __tablename__ = "la_payments"
    id = Column(String, primary_key=True, default=_id)
    matter_id = Column(String, ForeignKey("la_matters.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="GBP")
    provider = Column(String, nullable=False)  # govuk_pay|stripe|manual
    provider_payment_id = Column(String, nullable=True)
    status = Column(String, nullable=False)  # created|submitted|success|failed|cancelled
    payment_url = Column(String, nullable=True)
    failure_reason = Column(String, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    matter = relationship("LAMatter")

class LASLAEvent(Base):
    """SLA tracking and escalation events"""  
    __tablename__ = "la_sla_events"
    id = Column(String, primary_key=True, default=_id)
    matter_id = Column(String, ForeignKey("la_matters.id"), nullable=False)
    event_type = Column(String, nullable=False)  # sla_started|reminder_sent|escalated|completed
    due_date = Column(DateTime, nullable=False)
    actual_date = Column(DateTime, nullable=True)
    days_remaining = Column(Integer, nullable=True)
    escalation_level = Column(Integer, default=0)  # 0=normal, 1=at_risk, 2=overdue
    notification_sent = Column(String, nullable=False, default="false")
    created_at = Column(DateTime, server_default=func.now())
    
    matter = relationship("LAMatter")

class LAQAReview(Base):
    """Quality Assurance review workflow"""
    __tablename__ = "la_qa_reviews"
    id = Column(String, primary_key=True, default=_id) 
    matter_id = Column(String, ForeignKey("la_matters.id"), nullable=False)
    reviewer_id = Column(String, nullable=False)
    reviewer_name = Column(String, nullable=False)
    review_type = Column(String, nullable=False)  # standard|priority|random_sample
    status = Column(String, nullable=False, default="pending")  # pending|in_progress|approved|rejected|needs_changes
    
    # Review findings
    findings_approved = Column(Integer, default=0)
    findings_rejected = Column(Integer, default=0)
    answers_modified = Column(Integer, default=0)
    
    # Comments and changes
    reviewer_comments = Column(Text, nullable=True)
    change_summary = Column(Text, nullable=True)  # JSON of what was changed
    
    # Timestamps
    assigned_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    matter = relationship("LAMatter")

class LACommunication(Base):
    """Communications log for matters"""
    __tablename__ = "la_communications"
    id = Column(String, primary_key=True, default=_id)
    matter_id = Column(String, ForeignKey("la_matters.id"), nullable=False)
    communication_type = Column(String, nullable=False)  # email|sms|letter|portal_notification
    direction = Column(String, nullable=False)  # inbound|outbound
    recipient = Column(String, nullable=True)  # email/phone
    subject = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    template_used = Column(String, nullable=True)
    delivery_status = Column(String, nullable=False, default="pending")  # pending|sent|delivered|failed|bounced
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    matter = relationship("LAMatter")

class LAUser(Base):
    """LA staff users for assignment and QA"""
    __tablename__ = "la_users"
    id = Column(String, primary_key=True, default=_id)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # caseworker|reviewer|manager|admin
    team = Column(String, nullable=True)
    is_active = Column(String, nullable=False, default="true")
    can_review = Column(String, nullable=False, default="false")
    workload_capacity = Column(Integer, default=20)  # max concurrent matters
    created_at = Column(DateTime, server_default=func.now())
