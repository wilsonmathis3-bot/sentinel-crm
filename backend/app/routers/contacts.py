from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app import crud, schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.Contact])
def list_contacts(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    city: Optional[str] = None,
    industry: Optional[str] = None,
    min_score: Optional[float] = None,
    db: Session = Depends(get_db)
):
    return crud.get_contacts(db, skip=skip, limit=limit, search=search, city=city, industry=industry, min_score=min_score)

@router.post("/", response_model=schemas.Contact)
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db)):
    db_contact = crud.get_contact_by_email(db, email=contact.email)
    if db_contact:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_contact(db, contact)

@router.get("/{contact_id}", response_model=schemas.Contact)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    db_contact = crud.get_contact(db, contact_id)
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@router.put("/{contact_id}", response_model=schemas.Contact)
def update_contact(contact_id: int, contact: schemas.ContactUpdate, db: Session = Depends(get_db)):
    db_contact = crud.update_contact(db, contact_id, contact)
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@router.delete("/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    db_contact = crud.delete_contact(db, contact_id)
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted"}

@router.post("/{contact_id}/interactions", response_model=schemas.Interaction)
def create_interaction(contact_id: int, interaction: schemas.InteractionCreate, db: Session = Depends(get_db)):
    db_contact = crud.get_contact(db, contact_id)
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    interaction.contact_id = contact_id
    return crud.create_interaction(db, interaction)

@router.get("/{contact_id}/interactions", response_model=List[schemas.Interaction])
def get_interactions(contact_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_interactions(db, contact_id=contact_id, skip=skip, limit=limit)
