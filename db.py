import os, logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, declarative_base

# Safe default for Codespaces/dev
os.environ.setdefault("DATABASE_URL", "sqlite:///./dev.db")
DATABASE_URL = os.environ.get("DATABASE_URL")

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def _add_column(conn, table: str, ddl: str):
    try:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))
    except Exception as e:
        logging.getLogger(__name__).info("add column skipped (%s.%s): %s", table, ddl, e)

def init_db():
    # Import models to register mappers
    import models  # noqa

    # Create tables if missing
    # try:
    #     Base.metadata.create_all(engine)
    # except Exception as e:
    #     logging.getLogger(__name__).exception("create_all failed: %s", e)


        # Alembic now manages schema changes. No further action needed here.

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    logging.getLogger(__name__).info("DB init OK")
