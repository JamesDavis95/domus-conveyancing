import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db import Base  # reuse your existing Base from db.py

def _id():
    return str(uuid.uuid4())

class LAMatter(Base):
    __tablename__ = "la_matters"
    id = Column(String, primary_key=True, default=_id)
    ref = Column(String, nullable=False, unique=True)
    address = Column(String, nullable=True)
    uprn = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    orders = relationship("LAOrder", back_populates="matter", cascade="all, delete-orphan")
    findings = relationship("LAFinding", back_populates="matter", cascade="all, delete-orphan")
    risks = relationship("LARisk", back_populates="matter", cascade="all, delete-orphan")

class LAOrder(Base):
    __tablename__ = "la_orders"
    id = Column(String, primary_key=True, default=_id)
    matter_id = Column(String, ForeignKey("la_matters.id"), nullable=False)
    council_code = Column(String, nullable=False)
    types = Column(String, nullable=False)  # "LLC1,CON29"
    provider_ref = Column(String, nullable=True)
    status = Column(String, nullable=False, default="SUBMITTED")  # SUBMITTED|PENDING|READY|FAILED
    created_at = Column(DateTime, server_default=func.now())

    matter = relationship("LAMatter", back_populates="orders")
    documents = relationship("LADocument", back_populates="order", cascade="all, delete-orphan")

class LADocument(Base):
    __tablename__ = "la_documents"
    id = Column(String, primary_key=True, default=_id)
    order_id = Column(String, ForeignKey("la_orders.id"), nullable=False)
    kind = Column(String, nullable=False)  # LLC1|CON29|CON29O
    file_path = Column(String, nullable=False)
    content_type = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    order = relationship("LAOrder", back_populates="documents")

class LAFinding(Base):
    __tablename__ = "la_findings"
    id = Column(String, primary_key=True, default=_id)
    matter_id = Column(String, ForeignKey("la_matters.id"), nullable=False)
    key = Column(String, nullable=False)    # e.g. "con29.roads_footways.abutting_highway_adopted"
    value = Column(Text, nullable=True)     # JSON string
    evidence_file = Column(String, nullable=True)
    evidence_page = Column(Integer, nullable=True)
    confidence = Column(Integer, nullable=True)  # 0..100
    created_at = Column(DateTime, server_default=func.now())

    matter = relationship("LAMatter", back_populates="findings")

class LARisk(Base):
    __tablename__ = "la_risks"
    id = Column(String, primary_key=True, default=_id)
    matter_id = Column(String, ForeignKey("la_matters.id"), nullable=False)
    code = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # LOW|MEDIUM|HIGH
    message = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)     # JSON array string
    created_at = Column(DateTime, server_default=func.now())

    matter = relationship("LAMatter", back_populates="risks")
