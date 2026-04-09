"""
Ankole Framework - Health Router

GET /api/health -> public health check (no auth required)
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from sample_apps.api.dependencies import get_db
from sample_apps.api.schemas import HealthOut

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthOut)
def health_check(db: Session = Depends(get_db)):
    """
    Public health-check endpoint (no authentication required).
    Returns the API status, database connectivity, and version.
    """
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    return HealthOut(status="ok", db=db_status, version="2.0.0")
