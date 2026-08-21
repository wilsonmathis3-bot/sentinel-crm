from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app import models

def calculate_health_score(contact: models.Contact) -> float:
    """Simple formula: health = f(last_contact + response_rate)"""
    score = 100.0
    
    # Penalty for days since last contact
    if contact.last_contact:
        days_since = (datetime.utcnow() - contact.last_contact).days
        if days_since > 90:
            score -= 40
        elif days_since > 60:
            score -= 30
        elif days_since > 30:
            score -= 20
        elif days_since > 14:
            score -= 10
        elif days_since > 7:
            score -= 5
    else:
        # No contact ever
        score -= 50
    
    # Penalty for low response rate
    if contact.response_rate < 0.2:
        score -= 30
    elif contact.response_rate < 0.4:
        score -= 20
    elif contact.response_rate < 0.6:
        score -= 10
    
    # Bonus for recent engagement
    if contact.total_interactions >= 5 and contact.avg_response_time_hours <= 24:
        score += 10
    
    return max(0.0, min(100.0, score))

def calculate_all_health_scores(db: Session) -> int:
    """Recalculate health scores for all contacts"""
    contacts = db.query(models.Contact).all()
    updated = 0
    
    for contact in contacts:
        contact.health_score = calculate_health_score(contact)
        updated += 1
    
    db.commit()
    return updated
