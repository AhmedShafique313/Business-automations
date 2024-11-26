from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class CampaignType(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    SOCIAL = "social"

class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    campaign_type = Column(Enum(CampaignType))
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    content = Column(JSON)  # Stores email templates, SMS messages, etc.
    schedule = Column(JSON)  # Timing and frequency settings
    target_criteria = Column(JSON)  # Lead filtering criteria
    metadata = Column(JSON)  # Additional campaign settings
    stats = Column(JSON)  # Campaign performance metrics
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    scheduled_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    created_by = relationship("User", back_populates="campaigns")
    messages = relationship("CampaignMessage", back_populates="campaign")
    ab_tests = relationship("ABTest", back_populates="campaign")

class CampaignMessage(Base):
    __tablename__ = "campaign_messages"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    lead_id = Column(Integer, ForeignKey("leads.id"))
    message_type = Column(String)  # email, sms, whatsapp
    content = Column(JSON)
    status = Column(String)  # sent, delivered, opened, clicked, failed
    metadata = Column(JSON)  # Delivery details, tracking info
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="messages")
    lead = relationship("Lead")

class ABTest(Base):
    __tablename__ = "ab_tests"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    name = Column(String)
    variants = Column(JSON)  # Different content versions
    metrics = Column(JSON)  # Performance metrics for each variant
    winner = Column(String, nullable=True)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="ab_tests")
