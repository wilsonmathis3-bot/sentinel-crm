from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.models import DealStage, TaskStatus, TaskPriority, InteractionType

class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    industry: Optional[str] = None
    notes: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    industry: Optional[str] = None
    notes: Optional[str] = None

class Contact(ContactBase):
    id: int
    lead_score: float
    health_score: float
    created_at: datetime
    last_contact: Optional[datetime] = None
    response_rate: float
    total_interactions: int
    avg_response_time_hours: float
    
    class Config:
        from_attributes = True

class ContactList(Contact):
    pass

class InteractionBase(BaseModel):
    contact_id: int
    type: InteractionType
    summary: str
    response_time_hours: Optional[float] = None
    sentiment: Optional[float] = 0.0

class InteractionCreate(InteractionBase):
    pass

class Interaction(InteractionBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class DealBase(BaseModel):
    contact_id: int
    title: str
    value: float = 0.0
    stage: DealStage = DealStage.LEAD
    probability: float = 0.0
    expected_close: Optional[datetime] = None

class DealCreate(DealBase):
    pass

class DealUpdate(BaseModel):
    title: Optional[str] = None
    value: Optional[float] = None
    stage: Optional[DealStage] = None
    probability: Optional[float] = None
    expected_close: Optional[datetime] = None

class Deal(DealBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    contact_id: int
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None

class Task(TaskBase):
    id: int
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class DashboardMetrics(BaseModel):
    total_contacts: int
    total_deals: int
    total_value: float
    avg_deal_value: float
    win_rate: float
    active_tasks: int
    overdue_tasks: int
    avg_lead_score: float
    avg_health_score: float

class PipelineSummary(BaseModel):
    stage: str
    count: int
    value: float
    avg_probability: float

class AgentSuggestion(BaseModel):
    contact_id: int
    contact_name: str
    action: str
    reason: str
    priority: str
    suggested_date: Optional[datetime] = None

class NLQuery(BaseModel):
    query: str

class NLResponse(BaseModel):
    sql: str
    results: List[dict]
    summary: str

# Auth schemas
class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    passkey_enabled: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class LoginRequest(BaseModel):
    email: str
    password: str

class PasskeyRegistrationStart(BaseModel):
    user_id: str
    email: str
    name: str

class PasskeyRegistrationVerify(BaseModel):
    user_id: str
    response: dict
    device_name: Optional[str] = "Unknown Device"

class PasskeyAuthStart(BaseModel):
    credential_id: Optional[str] = None

class PasskeyAuthVerify(BaseModel):
    credential_id: str
    response: dict
