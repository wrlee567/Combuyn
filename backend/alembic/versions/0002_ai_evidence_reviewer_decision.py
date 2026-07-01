"""Add reviewer decision fields to AI evidence.

Revision ID: 0002_ai_evidence_reviewer_decision
Revises: 0001_initial
Create Date: 2026-06-30
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_ai_evidence_reviewer_decision"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ai_evidence_items",
        sa.Column("reviewer_decision", sa.String(length=64), nullable=False, server_default=""),
    )
    op.add_column(
        "ai_evidence_items",
        sa.Column("reviewer_notes", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("ai_evidence_items", "reviewer_notes")
    op.drop_column("ai_evidence_items", "reviewer_decision")
