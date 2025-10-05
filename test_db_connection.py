#!/usr/bin/env python3
"""Test database connection to debug production issues"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url

# Get the DATABASE_URL from environment
raw_url = os.getenv("DATABASE_URL", "").strip()
print(f"Raw DATABASE_URL: {raw_url[:50]}...")

if not raw_url:
    print("❌ DATABASE_URL not set")
    exit(1)

# Parse and normalize URL
url = make_url(raw_url)
print(f"Parsed scheme: {url.drivername}")
print(f"Host: {url.host}")
print(f"Database: {url.database}")
print(f"Query params: {url.query}")

# Normalize to psycopg
if url.drivername in ("postgres", "postgresql"):
    url = url.set(drivername="postgresql+psycopg")
    # Try different SSL modes
    ssl_modes = ["require", "prefer", "disable"]
    
    for ssl_mode in ssl_modes:
        try:
            test_url = url.update_query_dict({"sslmode": ssl_mode})
            print(f"\n🔄 Testing with sslmode={ssl_mode}")
            
            engine = create_engine(
                str(test_url),
                pool_pre_ping=True,
                pool_recycle=1800,
                echo=True,  # Show SQL queries
            )
            
            # Test connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                print(f"✅ Connection successful with sslmode={ssl_mode}")
                print(f"Test query result: {row}")
                break
                
        except Exception as e:
            print(f"❌ Failed with sslmode={ssl_mode}: {e}")
            
else:
    print(f"❌ Unexpected database scheme: {url.drivername}")