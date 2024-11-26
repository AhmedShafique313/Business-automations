from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class LeadStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"

class LeadSource(str, enum.Enum):
    WEBSITE = "website"
    REFERRAL = "referral"
    CAMPAIGN = "campaign"
    SOCIAL = "social"
    OTHER = "other"

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String, index=True)
    contact_name = Column(String)
    contact_email = Column(String)
    contact_phone = Column(String)
    website = Column(String)
    status = Column(Enum(LeadStatus), default=LeadStatus.NEW)
    source = Column(Enum(LeadSource), default=LeadSource.WEBSITE)
    lead_score = Column(Float, default=0.0)
    enriched_data = Column(JSON)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    activities = relationship("LeadActivity", back_populates="lead")
    tasks = relationship("Task", back_populates="lead")
    assigned_user = relationship("User", back_populates="assigned_leads")

class LeadActivity(Base):
    __tablename__ = "lead_activities"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    activity_type = Column(String)  # email_sent, email_opened, website_visit, etc.
    description = Column(String)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    lead = relationship("Lead", back_populates="activities")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    assigned_to = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    description = Column(String)
    due_date = Column(DateTime)
    status = Column(String)  # todo, in_progress, completed
    asana_task_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lead = relationship("Lead", back_populates="tasks")
    assigned_user = relationship("User", back_populates="tasks")
