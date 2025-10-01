"""
Production Database Initialization
Create the production database with all tables and initial data
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all models to ensure they're registered
from models import Base, User, Organization, Subscription, Payment, Usage
from production_data_layer import Project, BNGListing, LPAStatistic, Notification
from client_onboarding import OnboardingSession
from production_auth_complete import AuthService
from backend_auth_complete import UserRole, PlanType

def init_production_database():
    """Initialize production database with tables and seed data"""
    
    # Create database engine
    engine = create_engine("sqlite:///./production.db", connect_args={"check_same_thread": False})
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.email == "admin@domusplanning.co.uk").first()
        
        if not admin_user:
            print("Creating initial admin user...")
            
            # Create admin organization
            admin_org = Organization(
                name="Domus Platform Administration",
                plan_type="enterprise",  # Use string value directly
                subscription_status="active",
                trial_end=None  # No trial for admin
            )
            db.add(admin_org)
            db.flush()
            
            # Create admin user
            admin_user = User(
                email="admin@domusplanning.co.uk",
                name="Platform Administrator",
                hashed_password=AuthService.hash_password("admin123!"),  # Change this!
                role="super_admin",  # Use string value directly
                is_active=True,
                org_id=admin_org.id
            )
            db.add(admin_user)
            
            print("✅ Admin user created: admin@domusplanning.co.uk / admin123!")
            print("⚠️  IMPORTANT: Change the admin password immediately!")
        
        # Create sample LPA statistics if none exist
        lpa_count = db.query(LPAStatistic).count()
        if lpa_count == 0:
            print("Creating sample LPA statistics...")
            
            sample_lpas = [
                {
                    "lpa_name": "Westminster City Council",
                    "approval_rate_overall": 78.5,
                    "approval_rate_residential": 82.3,
                    "approval_rate_commercial": 71.2,
                    "avg_decision_time_weeks": 12.5,
                    "applications_per_month": 150
                },
                {
                    "lpa_name": "Camden Council",
                    "approval_rate_overall": 65.2,
                    "approval_rate_residential": 70.1,
                    "approval_rate_commercial": 58.9,
                    "avg_decision_time_weeks": 14.2,
                    "applications_per_month": 180
                },
                {
                    "lpa_name": "Tower Hamlets",
                    "approval_rate_overall": 85.7,
                    "approval_rate_residential": 89.2,
                    "approval_rate_commercial": 79.8,
                    "avg_decision_time_weeks": 10.8,
                    "applications_per_month": 120
                },
                {
                    "lpa_name": "Southwark Council",
                    "approval_rate_overall": 72.3,
                    "approval_rate_residential": 76.8,
                    "approval_rate_commercial": 65.1,
                    "avg_decision_time_weeks": 13.1,
                    "applications_per_month": 200
                },
                {
                    "lpa_name": "Oxford City Council",
                    "approval_rate_overall": 68.9,
                    "approval_rate_residential": 73.4,
                    "approval_rate_commercial": 61.7,
                    "avg_decision_time_weeks": 11.9,
                    "applications_per_month": 95
                }
            ]
            
            for lpa_data in sample_lpas:
                lpa = LPAStatistic(**lpa_data)
                db.add(lpa)
            
            print(f"✅ Created {len(sample_lpas)} LPA statistics")
        
        db.commit()
        print("✅ Production database initialized successfully!")
        
        # Print connection info
        print("\n📊 Database Status:")
        print(f"   Users: {db.query(User).count()}")
        print(f"   Organizations: {db.query(Organization).count()}")
        print(f"   LPA Statistics: {db.query(LPAStatistic).count()}")
        
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Initializing Domus Production Database...")
    init_production_database()
    print("✅ Database initialization complete!")