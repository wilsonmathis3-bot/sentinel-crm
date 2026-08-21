from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import crud, schemas

router = APIRouter()

@router.get("/metrics", response_model=schemas.DashboardMetrics)
def get_metrics(db: Session = Depends(get_db)):
    return crud.get_dashboard_metrics(db)

@router.get("/pipeline", response_model=List[schemas.PipelineSummary])
def get_pipeline(db: Session = Depends(get_db)):
    return crud.get_pipeline_summary(db)
