
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base

from settings import settings

DB_URL = settings.DATABASE_URL
connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
engine = create_engine(DB_URL, echo=False, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

class Matters(Base):
    __tablename__ = "matters"
    id = Column(Integer, primary_key=True)
    ref = Column(String(255))
    created_at = Column(String(64))  # ISO UTC
    council_id = Column(String(64), nullable=True)
    status = Column(String(32), default="done")  # pending/processing/done/failed

class Findings(Base):
    __tablename__ = "findings"
    id = Column(Integer, primary_key=True)
    matter_id = Column(Integer, ForeignKey("matters.id"))
    kind = Column(String(255))
    value = Column(Text)
    evidence_json = Column(Text, nullable=True)

class Risks(Base):
    __tablename__ = "risks"
    id = Column(Integer, primary_key=True)
    matter_id = Column(Integer, ForeignKey("matters.id"))
    code = Column(String(255))
    level = Column(String(32))
    evidence_json = Column(Text, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)
