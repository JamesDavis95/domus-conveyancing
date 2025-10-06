#!/usr/bin/env python3
"""
Bootstrap script for Domus AI Platform
Creates initial organizations, users, and sample data
"""

import os
import sys

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database_config import engine, SessionLocal
from models import (
    User, Organization, Membership, 
    Site, Analysis, Document, CreditWallet, SubmissionBundle
)
from datetime import datetime, timedelta
import hashlib

def create_initial_data():
    """Create initial organizations, users, and sample data for Domus AI"""
    
    session = SessionLocal()
    
    try:
        print("🚀 Bootstrapping Domus AI Platform...")
        
        # Check if data already exists
        existing_org = session.query(Organization).first()
        if existing_org:
            print("✓ Initial data already exists")
            return
        
        # Create Demo Users first
        demo_admin = User(
            email="admin@acme-dev.com",
            password_hash=hashlib.sha256("demo123".encode()).hexdigest(),  # Temporary simple hash
            full_name="Demo Administrator",
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow()
        )
        session.add(demo_admin)
        session.flush()
        
        demo_manager = User(
            email="manager@acme-dev.com", 
            password_hash=hashlib.sha256("demo123".encode()).hexdigest(),
            full_name="Site Manager",
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow()
        )
        session.add(demo_manager)
        session.flush()
        
        # Create Demo Organization with owner
        demo_org = Organization(
            name="Acme Development Ltd",
            slug="acme-dev",
            owner_user_id=demo_admin.id,
            created_at=datetime.utcnow()
        )
        session.add(demo_org)
        session.flush()
        
        # Create Memberships
        admin_membership = Membership(
            user_id=demo_admin.id,
            org_id=demo_org.id,
            role="Admin",
            is_active=True,
            joined_at=datetime.utcnow()
        )
        session.add(admin_membership)
        
        manager_membership = Membership(
            user_id=demo_manager.id,
            org_id=demo_org.id,
            role="Manager", 
            is_active=True,
            joined_at=datetime.utcnow()
        )
        session.add(manager_membership)
        
        # Create Credit Wallet
        credit_wallet = CreditWallet(
            org_id=demo_org.id,
            balance=1000,
            lifetime_purchased=1000,
            lifetime_used=0
        )
        session.add(credit_wallet)
        session.flush()
        
        # Create Sample Sites
        sites_data = [
            {
                "name": "Riverside Development Site",
                "address": "123 River Road, Manchester M1 2AB",
                "postcode": "M1 2AB",
                "site_area": 2500.0,
                "status": "analyzing"
            },
            {
                "name": "City Centre Mixed Use",
                "address": "456 High Street, Birmingham B1 1AA", 
                "postcode": "B1 1AA",
                "site_area": 1800.0,
                "status": "planning"
            },
            {
                "name": "Greenfield Housing Estate",
                "address": "789 Green Lane, Leeds LS1 3CD",
                "postcode": "LS1 3CD", 
                "site_area": 5000.0,
                "status": "submitted"
            }
        ]
        
        for site_data in sites_data:
            site = Site(
                name=site_data["name"],
                address=site_data["address"],
                postcode=site_data["postcode"],
                site_area=site_data["site_area"],
                status=site_data["status"],
                org_id=demo_org.id,
                created_by=demo_manager.id,
                created_at=datetime.utcnow() - timedelta(days=5)
            )
            session.add(site)
            session.flush()
            
            # Add AI Analysis for first site
            if site_data["status"] in ["planning", "submitted"]:
                analysis = Analysis(
                    site_id=site.id,
                    analysis_type="viability",
                    result_data={
                        "score": 82 if site_data["status"] == "planning" else 78,
                        "confidence": 0.89,
                        "factors": {
                            "location": 85,
                            "planning_history": 80,
                            "market_conditions": 82,
                            "infrastructure": 84
                        },
                        "recommendations": [
                            "Strong development potential",
                            "Consider sustainable design features",
                            "Review local planning policies"
                        ]
                    },
                    created_by=demo_manager.id,
                    created_at=datetime.utcnow() - timedelta(days=3)
                )
                session.add(analysis)
                site.ai_score = analysis.result_data["score"]
        
        session.commit()
        
        print("✅ Initial data created successfully!")
        print(f"   Organization: {demo_org.name}")
        print(f"   Admin user: {demo_admin.email} (password: demo123)")
        print(f"   Manager user: {demo_manager.email} (password: demo123)")
        print(f"   Sample sites: {len(sites_data)} created")
        print(f"   AI Credits: {credit_wallet.balance}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error creating initial data: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    # Ensure DATABASE_URL is set
    if not os.getenv("DATABASE_URL"):
        print("❌ DATABASE_URL environment variable is required")
        sys.exit(1)
    
    create_initial_data()
    print("\n🎯 Domus AI Platform bootstrap complete!")
    print("   You can now start the application and log in with the demo users.")