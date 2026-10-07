import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_name = Column(String(255), nullable=False)
    issuer_name = Column(String(255), nullable=False)
    issue_date = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    total_count = Column(Integer, nullable=False, default=0)
    processed_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    failure_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    certificates = relationship("CertificateRecord", back_populates="job", cascade="all, delete-orphan")

class CertificateRecord(Base):
    __tablename__ = "certificates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    file_path = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    job = relationship("Job", back_populates="certificates")
