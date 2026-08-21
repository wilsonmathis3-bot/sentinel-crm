from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app import crud, schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.Task])
def list_tasks(
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    contact_id: Optional[int] = None,
    overdue: bool = False,
    db: Session = Depends(get_db)
):
    return crud.get_tasks(db, skip=skip, limit=limit, status=status, contact_id=contact_id, overdue=overdue)

@router.post("/", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    return crud.create_task(db, task)

@router.get("/{task_id}", response_model=schemas.Task)
def get_task(task_id: int, db: Session = Depends(get_db)):
    db_task = crud.get_task(db, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@router.put("/{task_id}", response_model=schemas.Task)
def update_task(task_id: int, task: schemas.TaskUpdate, db: Session = Depends(get_db)):
    db_task = crud.update_task(db, task_id, task)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = crud.delete_task(db, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted"}
