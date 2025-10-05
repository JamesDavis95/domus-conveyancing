import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine.url import make_url

Base = declarative_base()

# Database configuration with URL normalization
raw_url = os.getenv("DATABASE_URL", "").strip()

if raw_url:
    # Accept postgres:// and normalize to postgresql+psycopg://
    url = make_url(raw_url)
    if url.drivername in ("postgres", "postgresql"):
        url = url.set(drivername="postgresql+psycopg")
        # For Render PostgreSQL, try sslmode=prefer first, then require
        if not url.query:
            url = url.update_query_dict({"sslmode": "prefer"})
        elif "sslmode" not in url.query:
            url = url.update_query_dict({"sslmode": "prefer"})

    # Guard against accidental https:// being pasted
    if url.drivername.startswith("http"):
        raise RuntimeError(
            f"Invalid DATABASE_URL (looks like a website, not a DB URL): {raw_url}"
        )

    if url.drivername.startswith("sqlite"):
        engine = create_engine(str(url), connect_args={"check_same_thread": False})
        print("Using SQLite database")
    else:
        # PostgreSQL configuration for production
        engine = create_engine(
            str(url),
            pool_pre_ping=True,
            pool_recycle=1800,
            future=True,
        )
        print(f"Using PostgreSQL database: {url.host}/{url.database}")
else:
    # Local SQLite fallback
    print("Using local SQLite database")
    DATABASE_URL = "sqlite:///./domus_planning.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

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