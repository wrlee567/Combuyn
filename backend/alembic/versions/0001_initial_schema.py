"""Initial schema baseline.

Builds the full schema from the ORM metadata so the emitted DDL is
dialect-correct (JSONB on PostgreSQL, JSON on SQLite). Subsequent schema
changes should use ``alembic revision --autogenerate`` against PostgreSQL.

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-20
"""

from __future__ import annotations

from alembic import op

# Register all models on Base.metadata.
import app.models  # noqa: F401
from app.database import Base

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
