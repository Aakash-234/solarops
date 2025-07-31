from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, Float
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    fields = Column(JSON)
    valid = Column(Boolean)
    issues = Column(JSON)
    confidence = Column(Float, default=0.0)  # ✅ new!
    ai_suggestion = Column(String)           # ✅ new!
    status = Column(String, default="pending")
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewer_comment = Column(String, nullable=True)
    audit_trail = Column(JSON, default=[])   # ✅ can store list of changes


