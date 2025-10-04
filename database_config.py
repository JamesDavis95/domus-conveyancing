"""
Database configuration for Domus Planning Platform
Handles both local SQLite and production PostgreSQL
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration with URL normalization
raw_url = os.getenv("DATABASE_URL", "").strip()

if raw_url:
    # Normalize legacy postgres:// scheme to postgresql+psycopg://
    url = make_url(raw_url)
    if url.drivername in ("postgres", "postgresql"):
        url = url.set(drivername="postgresql+psycopg")
    
    # Create engine with correct connect_args per backend
    if url.drivername.startswith("sqlite"):
        engine = create_engine(str(url), connect_args={"check_same_thread": False})
        print("Using SQLite database")
    else:
        engine = create_engine(
            str(url),
            pool_pre_ping=True,
            pool_recycle=300,
        )
        print("Using PostgreSQL database")
else:
    # Local SQLite fallback
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