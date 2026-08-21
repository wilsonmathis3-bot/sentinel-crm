from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import List, Dict
from app import models, schemas

def calculate_lead_score(contact: models.Contact) -> float:
    """Score leads based on response time + engagement"""
    score = 0.0
    
    # Engagement score (0-40): based on total interactions
    if contact.total_interactions >= 10:
        score += 40
    elif contact.total_interactions >= 5:
        score += 30
    elif contact.total_interactions >= 2:
        score += 20
    elif contact.total_interactions >= 1:
        score += 10
    
    # Response time score (0-30): faster is better
    if contact.avg_response_time_hours > 0:
        if contact.avg_response_time_hours <= 2:
            score += 30
        elif contact.avg_response_time_hours <= 8:
            score += 25
        elif contact.avg_response_time_hours <= 24:
            score += 20
        elif contact.avg_response_time_hours <= 48:
            score += 10
        else:
            score += 5
    else:
        score += 15  # Unknown - give middle score
    
    # Recency score (0-20): based on last contact
    if contact.last_contact:
        days_since = (datetime.utcnow() - contact.last_contact).days
        if days_since <= 3:
            score += 20
        elif days_since <= 7:
            score += 15
        elif days_since <= 14:
            score += 10
        elif days_since <= 30:
            score += 5
    
    # Response rate score (0-10)
    if contact.response_rate >= 0.8:
        score += 10
    elif contact.response_rate >= 0.5:
        score += 7
    elif contact.response_rate >= 0.2:
        score += 4
    elif contact.response_rate > 0:
        score += 2
    
    return min(score, 100.0)

def get_prospecting_suggestions(db: Session) -> List[Dict]:
    """Get high-potential leads that need attention"""
    contacts = db.query(models.Contact).order_by(desc(models.Contact.lead_score)).all()
    
    suggestions = []
    for contact in contacts[:20]:  # Top 20 leads
        # Recalculate score
        contact.lead_score = calculate_lead_score(contact)
        
        # Determine action based on score and recency
        if contact.lead_score >= 80 and (not contact.last_contact or (datetime.utcnow() - contact.last_contact).days > 7):
            suggestions.append({
                "contact_id": contact.id,
                "contact_name": f"{contact.first_name} {contact.last_name}",
                "action": "Hot lead - schedule call immediately",
                "reason": f"Lead score {contact.lead_score:.0f}, last contact {(datetime.utcnow() - contact.last_contact).days if contact.last_contact else 'never'} days ago",
                "priority": "HIGH",
                "suggested_date": datetime.utcnow() + timedelta(hours=4)
            })
        elif contact.lead_score >= 60 and (not contact.last_contact or (datetime.utcnow() - contact.last_contact).days > 14):
            suggestions.append({
                "contact_id": contact.id,
                "contact_name": f"{contact.first_name} {contact.last_name}",
                "action": "Warm lead - send personalized email",
                "reason": f"Lead score {contact.lead_score:.0f}, good engagement pattern",
                "priority": "MEDIUM",
                "suggested_date": datetime.utcnow() + timedelta(days=1)
            })
        elif contact.total_interactions >= 3 and contact.avg_response_time_hours <= 24 and (not contact.last_contact or (datetime.utcnow() - contact.last_contact).days > 21):
            suggestions.append({
                "contact_id": contact.id,
                "contact_name": f"{contact.first_name} {contact.last_name}",
                "action": "Re-engagement - quick check-in",
                "reason": f"Previously responsive (avg {contact.avg_response_time_hours:.0f}h), hasn't heard from us in {(datetime.utcnow() - contact.last_contact).days if contact.last_contact else 'never'} days",
                "priority": "MEDIUM",
                "suggested_date": datetime.utcnow() + timedelta(days=2)
            })
    
    db.commit()
    return suggestions[:10]  # Return top 10
