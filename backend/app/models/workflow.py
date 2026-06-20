"""Workflow Orchestration ORM models — Iteration 3.

A lightweight **durable state machine**. A :class:`WorkflowDefinition` stores a
JSON *blueprint* (states + transitions) that the UI renders visually. A
:class:`WorkflowInstance` is one running execution of that blueprint: its current
state and a JSONB ``context`` are persisted to Postgres after every transition,
so an instance survives a process crash and resumes exactly where it left off.

Every transition appends an immutable :class:`WorkflowEvent`. That ordered log is
both the audit trail and the durability mechanism — the engine can rebuild an
instance's current state purely by replaying its events. The log also records
**Saga compensation** steps when a running instance is rolled back.

    WorkflowDefinition 1───* WorkflowInstance 1───* WorkflowEvent
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.ccf import DEFAULT_ORG_ID, TimestampMixin, _uuid_pk
from app.models.types import JSONBType

# Instance lifecycle (distinct from the blueprint's own states).
INSTANCE_STATUSES = ["running", "completed", "compensated"]

# Event kinds appended to the durable log.
EVENT_KINDS = ["start", "transition", "complete", "compensation", "compensated"]


class WorkflowDefinition(Base, TimestampMixin):
    """A reusable workflow blueprint (states + transitions) stored as JSON."""

    __tablename__ = "workflow_definitions"
    __table_args__ = (
        UniqueConstraint("org_id", "key", name="uq_workflow_def_org_key"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)

    key: Mapped[str] = mapped_column(String(64))  # stable slug, e.g. "vendor_onboarding"
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")

    # JSON blueprint: {initial, states: [...], transitions: [...]}.
    blueprint: Mapped[dict] = mapped_column(JSONBType, default=dict)

    instances: Mapped[list[WorkflowInstance]] = relationship(
        back_populates="definition",
        cascade="all, delete-orphan",
    )


class WorkflowInstance(Base, TimestampMixin):
    """One durable execution of a :class:`WorkflowDefinition`."""

    __tablename__ = "workflow_instances"

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)
    definition_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_definitions.id", ondelete="CASCADE"), index=True
    )

    # What this run is about, e.g. "Northwind Payments onboarding".
    subject: Mapped[str] = mapped_column(String(255))

    current_state: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="running")

    # Free-form execution context persisted across transitions (Saga payload).
    context: Mapped[dict] = mapped_column(JSONBType, default=dict)

    definition: Mapped[WorkflowDefinition] = relationship(back_populates="instances")
    events: Mapped[list[WorkflowEvent]] = relationship(
        back_populates="instance",
        cascade="all, delete-orphan",
        order_by="WorkflowEvent.sequence",
    )


class WorkflowEvent(Base):
    """An immutable entry in an instance's transition log (the durable record)."""

    __tablename__ = "workflow_events"
    __table_args__ = (
        UniqueConstraint("instance_id", "sequence", name="uq_workflow_event_seq"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=DEFAULT_ORG_ID, index=True)
    instance_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_instances.id", ondelete="CASCADE"), index=True
    )

    sequence: Mapped[int] = mapped_column(Integer)  # 0-based order within instance
    kind: Mapped[str] = mapped_column(String(16))  # see EVENT_KINDS
    action: Mapped[str] = mapped_column(String(64), default="")
    from_state: Mapped[str] = mapped_column(String(64), default="")
    to_state: Mapped[str] = mapped_column(String(64), default="")
    note: Mapped[str] = mapped_column(Text, default="")

    instance: Mapped[WorkflowInstance] = relationship(back_populates="events")
