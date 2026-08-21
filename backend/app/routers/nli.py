from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas
from app.agents.nli import process_natural_language_query

router = APIRouter()

@router.post("/query", response_model=schemas.NLResponse)
def natural_language_query(query: schemas.NLQuery, db: Session = Depends(get_db)):
    return process_natural_language_query(db, query.query)
