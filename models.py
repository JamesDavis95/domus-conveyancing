from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, Float, Enum
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(enum.Enum):
    DEVELOPER = "developer"
    CONSULTANT = "consultant"
    LANDOWNER = "landowner"
    ADMIN = "admin"

class PlanType(enum.Enum):
    CORE = "core"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"

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
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.DEVELOPER)
    is_active = Column(Boolean, default=True)
    org_id = Column(Integer, ForeignKey("organizations.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    organization = relationship("Organization", back_populates="users")
    usage_records = relationship("Usage", back_populates="user")

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

# Add SessionLocal for SQLAlchemy sessions
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

engine = create_engine("sqlite:///./production.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
