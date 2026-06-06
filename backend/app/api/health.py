"""Health and readiness endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app import __version__
from app.database import get_db
from app.models.ccf import Framework

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Liveness check — process is up."""
    return {"status": "ok", "service": "combuyn", "version": __version__}


@router.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict:
    """Readiness check — database is reachable and seeded."""
    db.execute(text("SELECT 1"))
    framework_count = len(list(db.scalars(select(Framework))))
    return {"status": "ready", "frameworks": framework_count}
