#!/usr/bin/env python3
"""
Initialize Production Database
Creates all tables and sets up initial data for the production Domus platform
"""

from sqlalchemy import create_engine
from models import Base, User, Organization, PlanType, UserRole
from backend_auth import hash_password
from datetime import datetime, timedelta
import os

# Create production database
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./production.db')
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if 'sqlite' in DATABASE_URL else {})

def initialize_database():
    """Create all tables and initial data"""
    print("Initializing production database...")
    
    # Create all tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")
    
    # Create sample organization and admin user
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Create default organization
        org = Organization(
            name="Domus Admin",
            plan_type=PlanType.ENTERPRISE,
            created_at=datetime.utcnow(),
            trial_end=datetime.utcnow() + timedelta(days=30)
        )
        db.add(org)
        db.commit()
        
        # Create admin user
        admin_user = User(
            email="admin@domusplanning.co.uk",
            name="Domus Admin",
            hashed_password=hash_password("admin123"),  # Change this in production!
            role=UserRole.ADMIN,
            org_id=org.id,
            created_at=datetime.utcnow()
        )
        db.add(admin_user)
        db.commit()
        
        print(f"✓ Admin user created: admin@domusplanning.co.uk / admin123")
        print(f"✓ Organization created: {org.name} (ID: {org.id})")
        
    except Exception as e:
        print(f"Error creating initial data: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("Database initialization complete!")

if __name__ == "__main__":
    initialize_database()