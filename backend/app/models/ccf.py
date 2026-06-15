"""Common Control Framework (CCF) ORM models — Iteration 1.

The CCF is Combuyn's core idea: a single :class:`CommonControl` (e.g. "Data
Encryption at Rest") maps to many :class:`FrameworkRequirement` rows across
different :class:`Framework` standards (SOC 2, PCI DSS, NIST 800-53). Implement
the control once, satisfy many frameworks at once.

    Framework 1───* FrameworkRequirement *───* CommonControl
                          (via ControlRequirementMapping)

``org_id`` columns scope every row to a tenant. Full PostgreSQL Row-Level
Security is tracked for a later iteration; for now the application layer filters
by ``org_id``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Default tenant used until multi-org auth lands in a later iteration.
DEFAULT_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Framework(Base, TimestampMixin):
    """An overarching regulatory standard (e.g. SOC 2, PCI DSS, NIST 800-53)."""

    __tablename__ = "frameworks"
    __table_args__ = (UniqueConstraint("org_id", "key", name="uq_framework_org_key"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)

    key: Mapped[str] = mapped_column(String(64))  # stable slug, e.g. "soc2"
    name: Mapped[str] = mapped_column(String(255))
    version: Mapped[str] = mapped_column(String(64), default="")
    authority: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    # Categorize enterprise vs. medical so the medical subsystem stays segregated.
    category: Mapped[str] = mapped_column(String(32), default="enterprise")

    requirements: Mapped[list[FrameworkRequirement]] = relationship(
        back_populates="framework",
        cascade="all, delete-orphan",
    )


class FrameworkRequirement(Base, TimestampMixin):
    """A specific citation/criterion within a framework (e.g. NIST AC-2)."""

    __tablename__ = "framework_requirements"
    __table_args__ = (
        UniqueConstraint("framework_id", "citation", name="uq_requirement_citation"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)
    framework_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("frameworks.id", ondelete="CASCADE"), index=True
    )

    citation: Mapped[str] = mapped_column(String(64))  # e.g. "CC6.1", "SC-28"
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str] = mapped_column(Text, default="")

    framework: Mapped[Framework] = relationship(back_populates="requirements")
    mappings: Mapped[list[ControlRequirementMapping]] = relationship(
        back_populates="requirement",
        cascade="all, delete-orphan",
    )


class CommonControl(Base, TimestampMixin):
    """A unified control abstracting framework-specific language.

    One common control can satisfy many framework requirements simultaneously.
    """

    __tablename__ = "common_controls"
    __table_args__ = (UniqueConstraint("org_id", "key", name="uq_control_org_key"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)

    key: Mapped[str] = mapped_column(String(64))  # e.g. "CCF-CRYPTO-001"
    name: Mapped[str] = mapped_column(String(255))
    domain: Mapped[str] = mapped_column(String(128), default="")  # e.g. "Cryptography"
    description: Mapped[str] = mapped_column(Text, default="")

    mappings: Mapped[list[ControlRequirementMapping]] = relationship(
        back_populates="control",
        cascade="all, delete-orphan",
    )


class ControlRequirementMapping(Base, TimestampMixin):
    """Join row linking one common control to one framework requirement.

    Carries a ``relationship_type`` echoing SCF's STRM idea (a control may fully
    or partially satisfy a requirement).
    """

    __tablename__ = "control_requirement_mappings"
    __table_args__ = (
        UniqueConstraint(
            "control_id", "requirement_id", name="uq_mapping_control_requirement"
        ),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)

    control_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("common_controls.id", ondelete="CASCADE"), index=True
    )
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("framework_requirements.id", ondelete="CASCADE"), index=True
    )
    # "equal" | "subset" | "superset" | "intersects" (STRM-style relationship)
    relationship_type: Mapped[str] = mapped_column(String(32), default="intersects")

    control: Mapped[CommonControl] = relationship(back_populates="mappings")
    requirement: Mapped[FrameworkRequirement] = relationship(back_populates="mappings")
