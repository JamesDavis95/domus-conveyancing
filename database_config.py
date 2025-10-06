"""
Database configuration for Domus
Handles PostgreSQL URL normalization with psycopg v3 and SSL requirements
"""

import os
from urllib.parse import urlparse, parse_qs, urlencode
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

def normalize_database_url(url: str) -> str:
    """
    Normalize database URL for psycopg v3 with SSL requirements
    - Converts postgres:// or postgresql:// to postgresql+psycopg://
    - Ensures sslmode=require is present
    - Rejects HTTP URLs
    """
    if not url:
        raise ValueError("DATABASE_URL is required")
    
    if url.startswith(("http://", "https://")):
        raise ValueError("DATABASE_URL cannot be an HTTP URL")
    
    # Parse the URL
    parsed = urlparse(url)
    
    # Convert scheme to psycopg v3
    if parsed.scheme in ("postgres", "postgresql"):
        scheme = "postgresql+psycopg"
    else:
        scheme = parsed.scheme
    
    # Parse existing query parameters
    query_params = parse_qs(parsed.query)
    
    # Ensure sslmode=require is present
    if "sslmode" not in query_params:
        query_params["sslmode"] = ["require"]
    
    # Rebuild query string
    query_string = urlencode(query_params, doseq=True)
    
    # Reconstruct URL
    normalized_url = f"{scheme}://{parsed.netloc}{parsed.path}"
    if query_string:
        normalized_url += f"?{query_string}"
    
    return normalized_url

# Get and normalize DATABASE_URL from environment
DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL", ""))

# Create engine with Render-appropriate pool settings
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

def get_db():
    """Database session dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



def init_database():
    """Initialize database tables (dev only - production uses Alembic)"""
    try:
        from models import Base
        import os
        
        if os.getenv("ENV", "production") != "production":
            # Local/dev convenience only
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables initialized (dev mode)")
            return True
        else:
            print("✅ Production mode - trusting Alembic migrations")
            return True
    except Exception as e:
        print(f"⚠️ Database initialization error: {e}")
        return False