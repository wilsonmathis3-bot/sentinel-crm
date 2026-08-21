from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Optional, List

from app import models, schemas

def get_contact(db: Session, contact_id: int):
    return db.query(models.Contact).filter(models.Contact.id == contact_id).first()

def get_contact_by_email(db: Session, email: str):
    return db.query(models.Contact).filter(models.Contact.email == email).first()

def get_contacts(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None, 
                 city: Optional[str] = None, industry: Optional[str] = None, min_score: Optional[float] = None):
    query = db.query(models.Contact)
    
    if search:
        query = query.filter(
            (models.Contact.first_name.contains(search)) |
            (models.Contact.last_name.contains(search)) |
            (models.Contact.email.contains(search)) |
            (models.Contact.company.contains(search))
        )
    
    if city:
        query = query.filter(models.Contact.city == city)
    
    if industry:
        query = query.filter(models.Contact.industry == industry)
    
    if min_score:
        query = query.filter(models.Contact.lead_score >= min_score)
    
    return query.order_by(desc(models.Contact.lead_score)).offset(skip).limit(limit).all()

def create_contact(db: Session, contact: schemas.ContactCreate):
    db_contact = models.Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def update_contact(db: Session, contact_id: int, contact: schemas.ContactUpdate):
    db_contact = get_contact(db, contact_id)
    if not db_contact:
        return None
    
    for key, value in contact.dict(exclude_unset=True).items():
        setattr(db_contact, key, value)
    
    db.commit()
    db.refresh(db_contact)
    return db_contact

def delete_contact(db: Session, contact_id: int):
    db_contact = get_contact(db, contact_id)
    if db_contact:
        db.delete(db_contact)
        db.commit()
    return db_contact

def create_interaction(db: Session, interaction: schemas.InteractionCreate):
    db_interaction = models.Interaction(**interaction.dict())
    db.add(db_interaction)
    
    # Update contact stats
    contact = get_contact(db, interaction.contact_id)
    if contact:
        contact.total_interactions += 1
        contact.last_contact = datetime.utcnow()
        
        # Recalculate average response time
        if interaction.response_time_hours:
            if contact.avg_response_time_hours == 0:
                contact.avg_response_time_hours = interaction.response_time_hours
            else:
                contact.avg_response_time_hours = (
                    (contact.avg_response_time_hours * (contact.total_interactions - 1) + interaction.response_time_hours)
                    / contact.total_interactions
                )
    
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

def get_interactions(db: Session, contact_id: Optional[int] = None, skip: int = 0, limit: int = 100):
    query = db.query(models.Interaction)
    if contact_id:
        query = query.filter(models.Interaction.contact_id == contact_id)
    return query.order_by(desc(models.Interaction.created_at)).offset(skip).limit(limit).all()

def get_deal(db: Session, deal_id: int):
    return db.query(models.Deal).filter(models.Deal.id == deal_id).first()

def get_deals(db: Session, skip: int = 0, limit: int = 100, stage: Optional[str] = None, contact_id: Optional[int] = None):
    query = db.query(models.Deal)
    if stage:
        query = query.filter(models.Deal.stage == stage)
    if contact_id:
        query = query.filter(models.Deal.contact_id == contact_id)
    return query.order_by(desc(models.Deal.created_at)).offset(skip).limit(limit).all()

def create_deal(db: Session, deal: schemas.DealCreate):
    db_deal = models.Deal(**deal.dict())
    db.add(db_deal)
    db.commit()
    db.refresh(db_deal)
    return db_deal

def update_deal(db: Session, deal_id: int, deal: schemas.DealUpdate):
    db_deal = get_deal(db, deal_id)
    if not db_deal:
        return None
    
    for key, value in deal.dict(exclude_unset=True).items():
        setattr(db_deal, key, value)
    
    db_deal.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_deal)
    return db_deal

def delete_deal(db: Session, deal_id: int):
    db_deal = get_deal(db, deal_id)
    if db_deal:
        db.delete(db_deal)
        db.commit()
    return db_deal

def get_task(db: Session, task_id: int):
    return db.query(models.Task).filter(models.Task.id == task_id).first()

def get_tasks(db: Session, skip: int = 0, limit: int = 100, status: Optional[str] = None, 
              contact_id: Optional[int] = None, overdue: bool = False):
    query = db.query(models.Task)
    if status:
        query = query.filter(models.Task.status == status)
    if contact_id:
        query = query.filter(models.Task.contact_id == contact_id)
    if overdue:
        query = query.filter(
            models.Task.due_date < datetime.utcnow(),
            models.Task.status != models.TaskStatus.DONE
        )
    return query.order_by(models.Task.due_date).offset(skip).limit(limit).all()

def create_task(db: Session, task: schemas.TaskCreate):
    db_task = models.Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task(db: Session, task_id: int, task: schemas.TaskUpdate):
    db_task = get_task(db, task_id)
    if not db_task:
        return None
    
    for key, value in task.dict(exclude_unset=True).items():
        setattr(db_task, key, value)
    
    if task.status == schemas.TaskStatus.DONE and not db_task.completed_at:
        db_task.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int):
    db_task = get_task(db, task_id)
    if db_task:
        db.delete(db_task)
        db.commit()
    return db_task

def get_dashboard_metrics(db: Session):
    total_contacts = db.query(models.Contact).count()
    total_deals = db.query(models.Deal).count()
    total_value = db.query(func.sum(models.Deal.value)).scalar() or 0
    avg_deal_value = db.query(func.avg(models.Deal.value)).scalar() or 0
    
    won_deals = db.query(models.Deal).filter(models.Deal.stage == models.DealStage.CLOSED_WON).count()
    lost_deals = db.query(models.Deal).filter(models.Deal.stage == models.DealStage.CLOSED_LOST).count()
    win_rate = won_deals / (won_deals + lost_deals) if (won_deals + lost_deals) > 0 else 0
    
    active_tasks = db.query(models.Task).filter(models.Task.status != models.TaskStatus.DONE).count()
    overdue_tasks = db.query(models.Task).filter(
        models.Task.due_date < datetime.utcnow(),
        models.Task.status != models.TaskStatus.DONE
    ).count()
    
    avg_lead_score = db.query(func.avg(models.Contact.lead_score)).scalar() or 0
    avg_health_score = db.query(func.avg(models.Contact.health_score)).scalar() or 0
    
    return {
        "total_contacts": total_contacts,
        "total_deals": total_deals,
        "total_value": total_value,
        "avg_deal_value": round(avg_deal_value, 2),
        "win_rate": round(win_rate * 100, 1),
        "active_tasks": active_tasks,
        "overdue_tasks": overdue_tasks,
        "avg_lead_score": round(avg_lead_score, 1),
        "avg_health_score": round(avg_health_score, 1)
    }

def get_pipeline_summary(db: Session):
    stages = db.query(
        models.Deal.stage,
        func.count(models.Deal.id).label('count'),
        func.sum(models.Deal.value).label('value'),
        func.avg(models.Deal.probability).label('avg_probability')
    ).group_by(models.Deal.stage).all()
    
    return [
        {
            "stage": stage.stage.value,
            "count": stage.count,
            "value": stage.value or 0,
            "avg_probability": round((stage.avg_probability or 0) * 100, 1)
        }
        for stage in stages
    ]

# User CRUD
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, email: str, hashed_password: str, full_name: str):
    db_user = models.User(email=email, hashed_password=hashed_password, full_name=full_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_last_login(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if db_user:
        db_user.last_login = datetime.utcnow()
        db.commit()
    return db_user

def enable_passkey(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if db_user:
        db_user.passkey_enabled = True
        db.commit()
    return db_user

# Credential CRUD
def get_credential_by_credential_id(db: Session, credential_id: str):
    return db.query(models.Credential).filter(models.Credential.credential_id == credential_id).first()

def create_credential(db: Session, user_id: int, credential_id: str, public_key: str, device_name: str):
    db_cred = models.Credential(
        user_id=user_id,
        credential_id=credential_id,
        public_key=public_key,
        device_name=device_name
    )
    db.add(db_cred)
    db.commit()
    db.refresh(db_cred)
    return db_cred

def update_credential_sign_count(db: Session, credential_id: str, new_sign_count: int):
    db_cred = get_credential_by_credential_id(db, credential_id)
    if db_cred:
        db_cred.sign_count = new_sign_count
        db_cred.last_used = datetime.utcnow()
        db.commit()
    return db_cred
