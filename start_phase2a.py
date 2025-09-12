#!/usr/bin/env python3
"""
Phase 2A LA System Startup
"""
import sys
import os
sys.path.append('.')

print("🏛️ Phase 2A LA Workflow System")
print("===============================")

# Initialize database
print("📊 Initializing database...")
from db import engine, Base
from models import *
from la.models import *

Base.metadata.create_all(bind=engine)

from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
la_tables = [t for t in tables if t.startswith('la_')]
print(f"✅ Created {len(tables)} tables ({len(la_tables)} LA tables)")

if 'la_matters' in tables:
    columns = inspector.get_columns('la_matters')
    applicant_cols = [c['name'] for c in columns if 'applicant' in c['name']]
    print(f"👤 LAMatter applicant fields: {applicant_cols}")

print("🚀 Starting server...")

# Start server
os.system('/usr/local/python/current/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000')