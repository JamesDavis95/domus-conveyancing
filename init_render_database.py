#!/usr/bin/env python3
"""
Production Database Initialization for Render
Creates tables and initial admin user in PostgreSQL
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
try:
    from models import Base, User, Organization, UserRole, PlanType, SubscriptionStatus
    MODELS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Model import issue: {e}")
    # Define basic models inline for initialization
    from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum, Float
    from sqlalchemy.orm import declarative_base
    import enum
    
    Base = declarative_base()
    
    class UserRole(enum.Enum):
        DEVELOPER = "developer"
        CONSULTANT = "consultant" 
        LANDOWNER = "landowner"
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
    
    class Organization(Base):
        __tablename__ = "organizations"
        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        plan_type = Column(Enum(PlanType), default=PlanType.CORE)
        subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
        quota_limit = Column(Integer, default=100)
        created_at = Column(DateTime, default=datetime.utcnow)
    
    class User(Base):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True)
        email = Column(String, unique=True, index=True, nullable=False)
        name = Column(String, nullable=False)
        hashed_password = Column(String, nullable=False)
        role = Column(Enum(UserRole), default=UserRole.DEVELOPER)
        organization_id = Column(Integer, nullable=True)
        is_active = Column(Boolean, default=True)
        created_at = Column(DateTime, default=datetime.utcnow)
    
    MODELS_AVAILABLE = False

from datetime import datetime
import bcrypt

def init_render_database():
    """Initialize production database on Render"""
    
    print("🗄️ Initializing Domus Planning Platform Database...")
    
    # Get database URL from environment
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL environment variable not found!")
        print("   This script should run on Render during deployment.")
        return False
    
    # Handle PostgreSQL URL format
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    print(f"📡 Connecting to database...")
    
    try:
        # Create engine
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300
        )
        
        # Create all tables
        print("📋 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Create admin organization
        print("🏢 Creating admin organization...")
        admin_org = Organization(
            name="Domus Platform Admin",
            plan_type=PlanType.ENTERPRISE,
            subscription_status=SubscriptionStatus.ACTIVE,
            quota_limit=999999,
            created_at=datetime.utcnow()
        )
        db.add(admin_org)
        db.commit()
        db.refresh(admin_org)
        
        # Create admin user
        print("👤 Creating admin user...")
        hashed_password = bcrypt.hashpw("admin123!".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        admin_user = User(
            email="admin@domusplanning.co.uk",
            name="Platform Administrator",
            hashed_password=hashed_password,
            role=UserRole.SUPER_ADMIN,
            organization_id=admin_org.id,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(admin_user)
        db.commit()
        
        # Add sample data for LPA marketplace (optional)
        try:
            print("📊 Adding sample LPA data...")
            if MODELS_AVAILABLE:
                from models import LPAStatistic
            else:
                # Define LPAStatistic inline if needed
                class LPAStatistic(Base):
                    __tablename__ = "lpa_statistics"
                    id = Column(Integer, primary_key=True)
                    lpa_name = Column(String, nullable=False)
                    approval_rate = Column(Float, nullable=False)
                    average_decision_time = Column(Float, nullable=False)
                    total_applications = Column(Integer, nullable=False)
                    last_updated = Column(DateTime, default=datetime.utcnow)
            
            sample_lpas = [
                {"name": "Camden Council", "approval_rate": 0.78, "avg_time": 12.5, "total_apps": 1250},
                {"name": "Westminster City Council", "approval_rate": 0.82, "avg_time": 10.2, "total_apps": 980},
                {"name": "Tower Hamlets", "approval_rate": 0.71, "avg_time": 15.8, "total_apps": 1890},
                {"name": "Southwark Council", "approval_rate": 0.69, "avg_time": 18.1, "total_apps": 2100},
                {"name": "Lambeth Council", "approval_rate": 0.73, "avg_time": 14.3, "total_apps": 1560}
            ]
            
            for lpa_data in sample_lpas:
                lpa = LPAStatistic(
                    lpa_name=lpa_data["name"],
                    approval_rate=lpa_data["approval_rate"],
                    average_decision_time=lpa_data["avg_time"],
                    total_applications=lpa_data["total_apps"],
                    last_updated=datetime.utcnow()
                )
                db.add(lpa)
            
            db.commit()
            print("✅ LPA data added successfully")
            
        except Exception as lpa_error:
            print(f"⚠️ LPA data setup skipped: {lpa_error}")
            # Continue without LPA data
        db.close()
        
        print("✅ Database initialization complete!")
        print("")
        print("🔐 Admin Access:")
        print("   Email: admin@domusplanning.co.uk")
        print("   Password: admin123!")
        print("   ⚠️  Change this password immediately!")
        print("")
        print("🚀 Platform ready for deployment!")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = init_render_database()
    sys.exit(0 if success else 1)