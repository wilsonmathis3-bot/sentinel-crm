from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app import crud, schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.Deal])
def list_deals(
    skip: int = 0, 
    limit: int = 100, 
    stage: Optional[str] = None,
    contact_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    return crud.get_deals(db, skip=skip, limit=limit, stage=stage, contact_id=contact_id)

@router.post("/", response_model=schemas.Deal)
def create_deal(deal: schemas.DealCreate, db: Session = Depends(get_db)):
    return crud.create_deal(db, deal)

@router.get("/{deal_id}", response_model=schemas.Deal)
def get_deal(deal_id: int, db: Session = Depends(get_db)):
    db_deal = crud.get_deal(db, deal_id)
    if not db_deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return db_deal

@router.put("/{deal_id}", response_model=schemas.Deal)
def update_deal(deal_id: int, deal: schemas.DealUpdate, db: Session = Depends(get_db)):
    db_deal = crud.update_deal(db, deal_id, deal)
    if not db_deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return db_deal

@router.delete("/{deal_id}")
def delete_deal(deal_id: int, db: Session = Depends(get_db)):
    db_deal = crud.delete_deal(db, deal_id)
    if not db_deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return {"message": "Deal deleted"}
