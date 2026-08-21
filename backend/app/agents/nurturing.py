from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict
from app import models

def get_nurturing_suggestions(db: Session) -> List[Dict]:
    """Auto-suggest follow-up timing based on interaction patterns"""
    contacts = db.query(models.Contact).all()
    
    suggestions = []
    for contact in contacts:
        if not contact.last_contact:
            continue
        
        days_since = (datetime.utcnow() - contact.last_contact).days
        
        # Rule 1: High-value contacts (score > 70) need weekly touch
        if contact.lead_score >= 70 and days_since >= 5:
            suggestions.append({
                "contact_id": contact.id,
                "contact_name": f"{contact.first_name} {contact.last_name}",
                "action": "Weekly touch - high value contact",
                "reason": f"Lead score {contact.lead_score:.0f}, {days_since} days since last contact",
                "priority": "HIGH",
                "suggested_date": datetime.utcnow() + timedelta(days=1)
            })
        
        # Rule 2: Responsive contacts (avg response < 8h) get faster follow-up
        elif contact.avg_response_time_hours <= 8 and days_since >= 10:
            suggestions.append({
                "contact_id": contact.id,
                "contact_name": f"{contact.first_name} {contact.last_name}",
                "action": "Follow up - historically responsive",
                "reason": f"Average response time {contact.avg_response_time_hours:.0f}h, {days_since} days since last contact",
                "priority": "MEDIUM",
                "suggested_date": datetime.utcnow() + timedelta(days=2)
            })
        
        # Rule 3: Contacts with deals in pipeline need regular check-ins
        active_deals = [d for d in contact.deals if d.stage not in ['closed_won', 'closed_lost']]
        if active_deals and days_since >= 7:
            suggestions.append({
                "contact_id": contact.id,
                "contact_name": f"{contact.first_name} {contact.last_name}",
                "action": f"Pipeline check-in - {len(active_deals)} active deal(s)",
                "reason": f"Active deals worth ${sum(d.value for d in active_deals):,.0f}, {days_since} days since last contact",
                "priority": "HIGH",
                "suggested_date": datetime.utcnow() + timedelta(days=1)
            })
        
        # Rule 4: Dormant contacts (30+ days) need re-engagement
        elif days_since >= 30 and contact.total_interactions > 0:
            suggestions.append({
                "contact_id": contact.id,
                "contact_name": f"{contact.first_name} {contact.last_name}",
                "action": "Re-engagement - contact has gone cold",
                "reason": f"{days_since} days since last contact, {contact.total_interactions} previous interactions",
                "priority": "LOW",
                "suggested_date": datetime.utcnow() + timedelta(days=3)
            })
    
    # Sort by priority and suggested date
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    suggestions.sort(key=lambda x: (priority_order.get(x["priority"], 3), x["suggested_date"]))
    
    return suggestions[:10]
