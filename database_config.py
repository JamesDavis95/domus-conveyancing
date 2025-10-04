"""
Database configuration for Domus Planning Platform
Handles both local SQLite and production PostgreSQL
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    # Production PostgreSQL (Render)
    print("Using PostgreSQL database")
    engine = create_engine(DATABASE_URL)
else:
    # Local SQLite
    print("Using local SQLite database")
    DATABASE_URL = "sqlite:///./domus_planning.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_database():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Alias for compatibility
get_db = get_database

def init_database():
    """Initialize database tables"""
    try:
        from models import Base
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables initialized")
        return True
    except Exception as e:
        print(f"⚠️ Database initialization error: {e}")
        return False