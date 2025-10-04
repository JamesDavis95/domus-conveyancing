"""
Create database tables using SQLAlchemy models
"""

from database_config import engine
from models import Base

def create_all_tables():
    """Create all database tables"""
    try:
        print("Creating all database tables...")
        Base.metadata.create_all(engine)
        print("✅ All tables created successfully")
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        raise

if __name__ == "__main__":
    create_all_tables()