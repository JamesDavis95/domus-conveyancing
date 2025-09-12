#!/usr/bin/env python3
"""
Initialize the complete Phase 2A database schema
"""
import sys
sys.path.append('.')

from db import engine, Base
from models import *
from la.models import *

print("🗄️ Creating Phase 2A database schema...")

# Create all tables
Base.metadata.create_all(bind=engine)

from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"✅ Created {len(tables)} tables")

# Verify LA Matter structure  
if 'la_matters' in tables:
    columns = inspector.get_columns('la_matters')
    applicant_cols = [c['name'] for c in columns if 'applicant' in c['name']]
    print(f"👤 LAMatter has applicant fields: {applicant_cols}")
    
    # Check critical workflow fields
    workflow_fields = [c['name'] for c in columns if any(f in c['name'] for f in ['payment', 'sla', 'status', 'priority'])]
    print(f"⚙️ Workflow fields: {workflow_fields}")
    
print("🚀 Phase 2A database ready!")