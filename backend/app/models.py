from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum

class DealStage(str, enum.Enum):
    LEAD = "lead"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class InteractionType(str, enum.Enum):
    EMAIL = "email"
    CALL = "call"
    MEETING = "meeting"
    NOTE = "note"
    SMS = "sms"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    passkey_enabled = Column(Boolean, default=False)
    
    credentials = relationship("Credential", back_populates="user", cascade="all, delete")

class Credential(Base):
    __tablename__ = "credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    credential_id = Column(String, unique=True, index=True)
    public_key = Column(Text)
    sign_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    device_name = Column(String)
    
    user = relationship("User", back_populates="credentials")

class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    company = Column(String, index=True)
    city = Column(String, index=True)
    state = Column(String)
    industry = Column(String)
    lead_score = Column(Float, default=0.0)
    health_score = Column(Float, default=100.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_contact = Column(DateTime)
    response_rate = Column(Float, default=0.0)
    total_interactions = Column(Integer, default=0)
    avg_response_time_hours = Column(Float, default=0.0)
    notes = Column(Text)
    
    interactions = relationship("Interaction", back_populates="contact", cascade="all, delete")
    deals = relationship("Deal", back_populates="contact", cascade="all, delete")
    tasks = relationship("Task", back_populates="contact", cascade="all, delete")

class Interaction(Base):
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    type = Column(Enum(InteractionType))
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    response_time_hours = Column(Float)
    sentiment = Column(Float, default=0.0)
    
    contact = relationship("Contact", back_populates="interactions")

class Deal(Base):
    __tablename__ = "deals"
    
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    title = Column(String)
    value = Column(Float, default=0.0)
    stage = Column(Enum(DealStage), default=DealStage.LEAD)
    probability = Column(Float, default=0.0)
    expected_close = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    contact = relationship("Contact", back_populates="deals")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    title = Column(String)
    description = Column(Text)
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    contact = relationship("Contact", back_populates="tasks")
