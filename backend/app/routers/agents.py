from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import schemas
from app.agents.prospecting import get_prospecting_suggestions
from app.agents.nurturing import get_nurturing_suggestions
from app.agents.health_score import calculate_all_health_scores

router = APIRouter()

@router.get("/prospecting", response_model=List[schemas.AgentSuggestion])
def prospecting_agent(db: Session = Depends(get_db)):
    return get_prospecting_suggestions(db)

@router.get("/nurturing", response_model=List[schemas.AgentSuggestion])
def nurturing_agent(db: Session = Depends(get_db)):
    return get_nurturing_suggestions(db)

@router.post("/health-score")
def run_health_scores(db: Session = Depends(get_db)):
    updated = calculate_all_health_scores(db)
    return {"updated": updated}
