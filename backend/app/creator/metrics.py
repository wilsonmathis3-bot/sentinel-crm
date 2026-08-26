"""Metrics tracking and graduation logic.
Per-persona performance on shared/incubator account.
Data-driven graduation trigger (engagement drop >30% flagged).
"""
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models

# Graduation thresholds
GRADUATION_FOLLOWERS_MIN = int(os.getenv("GRADUATION_FOLLOWERS_MIN", "10000"))
GRADUATION_ENGAGEMENT_MIN = float(os.getenv("GRADUATION_ENGAGEMENT_MIN", "0.03"))
FLAG_ENGAGEMENT_DROP_PCT = float(os.getenv("FLAG_ENGAGEMENT_DROP_PCT", "0.30"))

def record_metric(db: Session, persona_id: int, platform: str,
                  followers: int = 0, likes: int = 0, views: int = 0,
                  comments: int = 0, shares: int = 0) -> models.CreatorMetric:
    """Record a daily metric snapshot for a persona."""
    # Calculate engagement rate
    engagement_rate = 0.0
    if followers > 0:
        engagement_rate = (likes + comments + shares) / followers
    
    # Check for flag (engagement drop >30% week-over-week)
    flagged = False
    flag_reason = None
    
    last_week = db.query(models.CreatorMetric).filter(
        models.CreatorMetric.persona_id == persona_id,
        models.CreatorMetric.platform == platform,
        models.CreatorMetric.date >= datetime.now(timezone.utc) - timedelta(days=7)
    ).order_by(models.CreatorMetric.date.desc()).first()
    
    if last_week and last_week.engagement_rate > 0:
        drop = (last_week.engagement_rate - engagement_rate) / last_week.engagement_rate
        if drop > FLAG_ENGAGEMENT_DROP_PCT:
            flagged = True
            flag_reason = f"Engagement dropped {drop*100:.1f}% week-over-week"
    
    metric = models.CreatorMetric(
        persona_id=persona_id,
        platform=platform,
        followers=followers,
        likes=likes,
        views=views,
        comments=comments,
        shares=shares,
        engagement_rate=engagement_rate,
        flagged=flagged,
        flag_reason=flag_reason,
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


def check_graduation_eligibility(db: Session, persona_id: int) -> Dict[str, Any]:
    """Check if a persona is eligible for graduation from incubator.
    
    Returns dict with eligible (bool), reasons (list), metrics (dict).
    """
    persona = db.query(models.Persona).filter(models.Persona.id == persona_id).first()
    if not persona:
        return {"eligible": False, "reasons": ["Persona not found"]}
    
    if persona.lifecycle != models.PersonaLifecycle.INCUBATING:
        return {
            "eligible": False,
            "reasons": [f"Persona is {persona.lifecycle.value}, not incubating"],
        }
    
    # Get latest metrics for persona on incubator account
    latest = db.query(models.CreatorMetric).filter(
        models.CreatorMetric.persona_id == persona_id,
    ).order_by(models.CreatorMetric.date.desc()).first()
    
    reasons = []
    metrics_summary = {}
    
    if latest:
        metrics_summary = {
            "followers": latest.followers,
            "engagement_rate": round(latest.engagement_rate, 4),
            "date": latest.date.isoformat() if latest.date else None,
        }
        
        if latest.followers >= GRADUATION_FOLLOWERS_MIN:
            reasons.append(f"Followers: {latest.followers} >= {GRADUATION_FOLLOWERS_MIN}")
        else:
            reasons.append(f"Followers: {latest.followers} < {GRADUATION_FOLLOWERS_MIN}")
        
        if latest.engagement_rate >= GRADUATION_ENGAGEMENT_MIN:
            reasons.append(f"Engagement: {latest.engagement_rate:.2%} >= {GRADUATION_ENGAGEMENT_MIN:.2%}")
        else:
            reasons.append(f"Engagement: {latest.engagement_rate:.2%} < {GRADUATION_ENGAGEMENT_MIN:.2%}")
    else:
        reasons.append("No metrics recorded yet")
    
    eligible = (
        latest and
        latest.followers >= GRADUATION_FOLLOWERS_MIN and
        latest.engagement_rate >= GRADUATION_ENGAGEMENT_MIN
    )
    
    return {
        "eligible": eligible,
        "reasons": reasons,
        "metrics": metrics_summary,
    }


def graduate_persona(db: Session, persona_id: int, instagram_account_id: int) -> Dict[str, Any]:
    """Graduate a persona from incubator to independent account.
    
    Args:
        persona_id: persona to graduate
        instagram_account_id: new independent Instagram account
    """
    persona = db.query(models.Persona).filter(models.Persona.id == persona_id).first()
    if not persona:
        return {"status": "error", "message": "Persona not found"}
    
    if persona.lifecycle != models.PersonaLifecycle.INCUBATING:
        return {
            "status": "error",
            "message": f"Cannot graduate persona in {persona.lifecycle.value} state",
        }
    
    # Update lifecycle
    persona.lifecycle = models.PersonaLifecycle.INDEPENDENT
    persona.instagram_account_id = instagram_account_id
    
    db.commit()
    
    return {
        "status": "ok",
        "persona_id": persona_id,
        "new_lifecycle": persona.lifecycle.value,
        "instagram_account_id": instagram_account_id,
        "message": "Persona graduated to independent account. Rookie can now enter incubator.",
    }


def get_flagged_metrics(db: Session) -> List[Dict[str, Any]]:
    """Get all flagged metrics for daily review."""
    flagged = db.query(models.CreatorMetric).filter(
        models.CreatorMetric.flagged == True
    ).order_by(models.CreatorMetric.date.desc()).all()
    
    return [
        {
            "id": m.id,
            "persona_id": m.persona_id,
            "persona_name": m.persona.name if m.persona else None,
            "platform": m.platform,
            "date": m.date.isoformat() if m.date else None,
            "engagement_rate": m.engagement_rate,
            "flag_reason": m.flag_reason,
        }
        for m in flagged
    ]


def get_metrics_summary(db: Session, persona_id: int = None,
                        days: int = 30) -> Dict[str, Any]:
    """Get metrics summary for persona(s) over last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    query = db.query(models.CreatorMetric).filter(models.CreatorMetric.date >= cutoff)
    if persona_id:
        query = query.filter(models.CreatorMetric.persona_id == persona_id)
    
    metrics = query.all()
    
    if not metrics:
        return {"status": "no_data", "message": "No metrics in period"}
    
    total_likes = sum(m.likes for m in metrics)
    total_views = sum(m.views for m in metrics)
    total_comments = sum(m.comments for m in metrics)
    total_shares = sum(m.shares for m in metrics)
    avg_engagement = sum(m.engagement_rate for m in metrics) / len(metrics) if metrics else 0
    flagged_count = sum(1 for m in metrics if m.flagged)
    
    return {
        "status": "ok",
        "period_days": days,
        "persona_id": persona_id,
        "total_posts": len(metrics),
        "total_likes": total_likes,
        "total_views": total_views,
        "total_comments": total_comments,
        "total_shares": total_shares,
        "avg_engagement_rate": round(avg_engagement, 4),
        "flagged_count": flagged_count,
    }
