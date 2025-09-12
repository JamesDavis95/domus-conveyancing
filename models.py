from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Matters(Base):
    __tablename__ = "matters"
    id = Column(Integer, primary_key=True)
    ref = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="created")

    files = relationship("Files", back_populates="matter", cascade="all, delete-orphan")
    findings = relationship("Findings", back_populates="matter", cascade="all, delete-orphan")
    risks = relationship("Risks", back_populates="matter", cascade="all, delete-orphan")

class Files(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    kind = Column(String, nullable=True, default="search")
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    ocr_applied = Column(Boolean, default=False)

    matter = relationship("Matters", back_populates="files")

class Findings(Base):
    __tablename__ = "findings"
    id = Column(Integer, primary_key=True)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(Text, nullable=False)
    confidence = Column(Integer, default=1)

    matter = relationship("Matters", back_populates="findings")

class Risks(Base):
    __tablename__ = "risks"
    id = Column(Integer, primary_key=True)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    code = Column(String, nullable=False)
    level = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    matter = relationship("Matters", back_populates="risks")
# Add SessionLocal for SQLAlchemy sessions
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
