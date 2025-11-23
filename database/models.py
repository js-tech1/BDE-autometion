"""
Database models for BDE Automation System
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()


class LeadStatus(enum.Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    MEETING_SCHEDULED = "meeting_scheduled"
    NEGOTIATING = "negotiating"
    WON = "won"
    LOST = "lost"


class EmailStatus(enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    FAILED = "failed"
    OPENED = "opened"
    REPLIED = "replied"


class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    contact_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)  # Removed unique=True for testing
    phone = Column(String(50))
    industry = Column(String(100))
    company_size = Column(String(50))
    revenue = Column(String(50))
    location = Column(String(255))
    
    # AI Analysis Fields
    lead_score = Column(Float, default=0.0)
    qualification_notes = Column(Text)
    pain_points = Column(Text)
    budget_estimate = Column(String(100))
    decision_timeline = Column(String(100))
    
    # Status
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.NEW, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_contacted_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<Lead(id={self.id}, company={self.company_name}, status={self.status})>"


class Email(Base):
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, nullable=False, index=True)
    
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    recipient_email = Column(String(255), nullable=False)
    
    # Email type: initial, follow_up, pitch, etc.
    email_type = Column(String(50), default="initial", index=True)
    
    status = Column(SQLEnum(EmailStatus), default=EmailStatus.DRAFT, index=True)
    
    # Tracking
    sent_at = Column(DateTime(timezone=True))
    opened_at = Column(DateTime(timezone=True))
    replied_at = Column(DateTime(timezone=True))
    
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Email(id={self.id}, lead_id={self.lead_id}, status={self.status})>"


class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, nullable=False, index=True)
    
    title = Column(String(500), nullable=False)
    description = Column(Text)
    
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=30)
    
    meeting_link = Column(String(500))
    location = Column(String(500))
    
    status = Column(String(50), default="scheduled")  # scheduled, completed, cancelled
    
    # Meeting outcomes
    notes = Column(Text)
    next_steps = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Meeting(id={self.id}, lead_id={self.lead_id}, scheduled_at={self.scheduled_at})>"


class Activity(Base):
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, nullable=False, index=True)
    
    activity_type = Column(String(50), nullable=False)  # email_sent, meeting_scheduled, call_made, etc.
    description = Column(Text)
    activity_metadata = Column(Text)  # JSON string for additional data (renamed from 'metadata')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Activity(id={self.id}, lead_id={self.lead_id}, type={self.activity_type})>"
