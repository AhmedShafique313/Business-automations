from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    SALES_REP = "sales_rep"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(Enum(UserRole))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # API Integration settings
    asana_user_id = Column(String, nullable=True)
    google_refresh_token = Column(String, nullable=True)

    # Relationships
    assigned_leads = relationship("Lead", back_populates="assigned_user")
    tasks = relationship("Task", back_populates="assigned_user")
    campaigns = relationship("Campaign", back_populates="created_by")
