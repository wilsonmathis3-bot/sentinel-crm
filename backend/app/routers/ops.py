"""Ops router — EOD sweep and operational endpoints."""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_active_user
from app import models

router = APIRouter()


@router.get("/eod-latest")
async def get_latest_eod_sweep(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get the most recent EOD sweep results."""
    sweep = db.query(models.EodSweep).order_by(models.EodSweep.swept_at.desc()).first()
    if not sweep:
        return {"status": "no_data", "message": "No EOD sweeps recorded yet"}
    return {
        "status": "ok",
        "data": {
            "id": sweep.id,
            "swept_at": sweep.swept_at.isoformat() if sweep.swept_at else None,
            "summary": json.loads(sweep.summary) if sweep.summary else {},
            "checks": json.loads(sweep.checks) if sweep.checks else [],
        }
    }
