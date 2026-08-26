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

class PersonaStatus(str, enum.Enum):
    DRAFT = "draft"
    CHARACTER_LOCK = "character_lock"
    INCUBATING = "incubating"
    ACTIVE = "active"
    GRADUATED = "graduated"
    ARCHIVED = "archived"

class AssetKind(str, enum.Enum):
    CANDIDATE = "candidate"
    CANONICAL = "canonical"
    CONTENT = "content"

class JobPurpose(str, enum.Enum):
    CHARACTER_LOCK = "character_lock"
    LORA_TRAIN = "lora_train"
    CONTENT_BATCH = "content_batch"
    INCUBATOR_POST = "incubator_post"

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

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

class EodSweep(Base):
    __tablename__ = "eod_sweeps"
    
    id = Column(Integer, primary_key=True, index=True)
    swept_at = Column(DateTime, default=datetime.utcnow)
    summary = Column(Text)
    checks = Column(Text)

# ---------------------------------------------------------------------------
# Creator Studio models
# ---------------------------------------------------------------------------

class Persona(Base):
    __tablename__ = "personas"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    archetype = Column(String)
    brief_json = Column(Text)
    status = Column(Enum(PersonaStatus), default=PersonaStatus.DRAFT)
    leonardo_model_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    assets = relationship("CreatorAsset", back_populates="persona", cascade="all, delete")
    jobs = relationship("GenerationJob", back_populates="persona", cascade="all, delete")
    portfolio_sets = relationship("PortfolioSet", back_populates="persona", cascade="all, delete")
    portfolio_items = relationship("PortfolioItem", back_populates="persona", cascade="all, delete")
    lifecycle_events = relationship("PersonaLifecycleEvent", back_populates="persona", cascade="all, delete")

class CreatorAsset(Base):
    __tablename__ = "creator_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    persona_id = Column(Integer, ForeignKey("personas.id"))
    kind = Column(Enum(AssetKind), default=AssetKind.CANDIDATE)
    leonardo_generation_id = Column(String)
    file_path = Column(String)
    prompt = Column(Text)
    credits_used = Column(Float, default=0.0)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    persona = relationship("Persona", back_populates="assets")

class GenerationJob(Base):
    __tablename__ = "generation_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    persona_id = Column(Integer, ForeignKey("personas.id"))
    purpose = Column(Enum(JobPurpose))
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    leonardo_ids_json = Column(Text)
    credits_used = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    
    persona = relationship("Persona", back_populates="jobs")

class PortfolioSet(Base):
    __tablename__ = "portfolio_sets"

    id = Column(Integer, primary_key=True, index=True)
    persona_id = Column(Integer, ForeignKey("personas.id"))
    title = Column(String, nullable=False)
    theme = Column(String)
    week_label = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    persona = relationship("Persona", back_populates="portfolio_sets")
    items = relationship("PortfolioItem", back_populates="portfolio_set")

class PortfolioItem(Base):
    __tablename__ = "portfolio_items"

    id = Column(Integer, primary_key=True, index=True)
    persona_id = Column(Integer, ForeignKey("personas.id"))
    asset_id = Column(Integer, ForeignKey("creator_assets.id"))
    set_id = Column(Integer, ForeignKey("portfolio_sets.id"), nullable=True)
    caption = Column(Text)
    hashtags = Column(Text)
    featured = Column(Boolean, default=False)
    status = Column(String, default="draft")  # draft | queued | published | archived
    platform = Column(String)
    published_at = Column(DateTime, nullable=True)
    likes = Column(Integer, default=0)
    views = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    persona = relationship("Persona", back_populates="portfolio_items")
    asset = relationship("CreatorAsset")
    portfolio_set = relationship("PortfolioSet", back_populates="items")

# ---------------------------------------------------------------------------
# Phase B: Shared IG Incubator + Persona Lifecycle
# ---------------------------------------------------------------------------

class IncubatorAccount(Base):
    __tablename__ = "incubator_accounts"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, default="instagram")  # instagram | tiktok | x
    handle = Column(String, nullable=False, unique=True)
    display_name = Column(String)
    bio = Column(Text)
    follower_count = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    status = Column(String, default="active")  # active | paused | retired
    created_at = Column(DateTime, default=datetime.utcnow)

class PersonaLifecycleEvent(Base):
    __tablename__ = "persona_lifecycle_events"

    id = Column(Integer, primary_key=True, index=True)
    persona_id = Column(Integer, ForeignKey("personas.id"))
    from_status = Column(String)
    to_status = Column(String)
    trigger = Column(String)  # manual | follower_threshold | engagement_threshold | time_based | revenue_threshold
    trigger_data_json = Column(Text)  # {"follower_count": 10000, "engagement_rate": 0.05}
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    persona = relationship("Persona", back_populates="lifecycle_events")
