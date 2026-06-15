"""Vendor ORM model — Iteration 2 (TPRM).

A vendor moves through the TPRM lifecycle (sourcing → onboarding → assessment →
management → monitoring → offboarding). Its *inherent* risk (before controls) is
computed at intake from four factors and stored alongside a per-factor
breakdown. Dynamic security questionnaire answers live in a JSONB column so the
questionnaire can evolve without schema migrations.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.ccf import DEFAULT_ORG_ID, TimestampMixin, _uuid_pk
from app.models.types import JSONBType

# TPRM lifecycle phases from the blueprint.
LIFECYCLE_PHASES = [
    "sourcing",
    "onboarding",
    "assessment",
    "management",
    "monitoring",
    "offboarding",
]


class Vendor(Base, TimestampMixin):
    __tablename__ = "vendors"

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)

    name: Mapped[str] = mapped_column(String(255))
    contact_name: Mapped[str] = mapped_column(String(255), default="")
    contact_email: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")

    # Inherent-risk input factors (validated against risk_scoring lookups).
    industry: Mapped[str] = mapped_column(String(64), default="other")
    data_classification: Mapped[str] = mapped_column(String(32), default="internal")
    network_connectivity: Mapped[str] = mapped_column(String(32), default="limited")
    geography: Mapped[str] = mapped_column(String(32), default="domestic")

    # Computed inherent risk (before controls).
    inherent_risk_score: Mapped[int] = mapped_column(Integer, default=0)
    inherent_risk_tier: Mapped[str] = mapped_column(String(16), default="Low")
    risk_breakdown: Mapped[dict] = mapped_column(JSONBType, default=dict)

    # Where the vendor sits in the TPRM lifecycle.
    lifecycle_status: Mapped[str] = mapped_column(String(32), default="sourcing")

    # Dynamic security questionnaire answers: {question_id: answer}.
    questionnaire_responses: Mapped[dict] = mapped_column(JSONBType, default=dict)
