"""Seed the demo user used for mock-first authentication."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.auth import hash_password
from app.config import get_settings
from app.models.ccf import DEFAULT_ORG_ID
from app.models.user import DemoUser


def seed_demo_user(db: Session) -> bool:
    """Upsert the demo user; return True if it was created."""
    settings = get_settings()
    existing = db.query(DemoUser).filter_by(email=settings.demo_user_email).first()
    if existing:
        return False
    user = DemoUser(
        email=settings.demo_user_email,
        password_hash=hash_password(settings.demo_user_password),
        org_id=DEFAULT_ORG_ID,
    )
    db.add(user)
    db.commit()
    return True
