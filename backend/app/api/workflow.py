"""Workflow Orchestration API — Iteration 3.

List blueprints, launch durable instances, advance them through their state
machine, and roll them back via Saga compensation. Every transition is persisted
to the event log and broadcast to observers (mock Slack notifier).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.workflow import WorkflowDefinition, WorkflowInstance
from app.schemas.workflow import (
    AdvanceRequest,
    CompensateRequest,
    InstanceCreate,
    TransitionOption,
    WorkflowDefinitionDetail,
    WorkflowDefinitionSummary,
    WorkflowEventOut,
    WorkflowInstanceDetail,
    WorkflowInstanceSummary,
)
from app.services import workflow_engine as engine
from app.services import workflow_runtime
from app.services.notifications import notifier, slack

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


def _detail(instance: WorkflowInstance) -> WorkflowInstanceDetail:
    definition = instance.definition
    blueprint = definition.blueprint
    if instance.status == "running":
        actions = [
            TransitionOption(action=t.action, target=t.target, compensation=t.compensation)
            for t in engine.available_actions(blueprint, instance.current_state)
        ]
    else:
        actions = []
    return WorkflowInstanceDetail(
        id=instance.id,
        definition_id=instance.definition_id,
        subject=instance.subject,
        current_state=instance.current_state,
        status=instance.status,
        definition_key=definition.key,
        definition_name=definition.name,
        context=instance.context,
        blueprint=blueprint,
        events=[WorkflowEventOut.model_validate(e) for e in instance.events],
        available_actions=actions,
    )


def _load_instance(db: Session, instance_id: uuid.UUID) -> WorkflowInstance:
    instance = db.scalar(
        select(WorkflowInstance)
        .where(WorkflowInstance.id == instance_id)
        .options(
            selectinload(WorkflowInstance.definition),
            selectinload(WorkflowInstance.events),
        )
    )
    if instance is None:
        raise HTTPException(status_code=404, detail="Workflow instance not found")
    return instance


# Static routes first so they aren't captured by the UUID path param.
@router.get("/definitions", response_model=list[WorkflowDefinitionSummary])
def list_definitions(db: Session = Depends(get_db)) -> list[WorkflowDefinitionSummary]:
    stmt = select(WorkflowDefinition).order_by(WorkflowDefinition.name)
    return [WorkflowDefinitionSummary.model_validate(d) for d in db.scalars(stmt)]


@router.get("/definitions/{definition_id}", response_model=WorkflowDefinitionDetail)
def get_definition(
    definition_id: uuid.UUID, db: Session = Depends(get_db)
) -> WorkflowDefinitionDetail:
    definition = db.get(WorkflowDefinition, definition_id)
    if definition is None:
        raise HTTPException(status_code=404, detail="Workflow definition not found")
    return WorkflowDefinitionDetail.model_validate(definition)


@router.get("/notifications")
def notifications(limit: int = 50) -> dict:
    """Recent transition notifications the mock Slack notifier would have posted."""
    return {"channel": slack.channel, "notifications": slack.recent(limit)}


@router.get("", response_model=list[WorkflowInstanceSummary])
def list_instances(db: Session = Depends(get_db)) -> list[WorkflowInstanceSummary]:
    stmt = select(WorkflowInstance).order_by(WorkflowInstance.subject)
    return [WorkflowInstanceSummary.model_validate(i) for i in db.scalars(stmt)]


@router.post("", response_model=WorkflowInstanceDetail, status_code=201)
def create_instance(
    payload: InstanceCreate, db: Session = Depends(get_db)
) -> WorkflowInstanceDetail:
    definition = db.scalar(
        select(WorkflowDefinition).where(WorkflowDefinition.key == payload.definition_key)
    )
    if definition is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown workflow definition '{payload.definition_key}'.",
        )
    instance = workflow_runtime.start_instance(
        db, definition, payload.subject, payload.context, notifier=notifier
    )
    db.commit()
    db.refresh(instance)
    return _detail(instance)


@router.get("/{instance_id}", response_model=WorkflowInstanceDetail)
def get_instance(
    instance_id: uuid.UUID, db: Session = Depends(get_db)
) -> WorkflowInstanceDetail:
    return _detail(_load_instance(db, instance_id))


@router.post("/{instance_id}/advance", response_model=WorkflowInstanceDetail)
def advance(
    instance_id: uuid.UUID,
    payload: AdvanceRequest,
    db: Session = Depends(get_db),
) -> WorkflowInstanceDetail:
    instance = _load_instance(db, instance_id)
    try:
        workflow_runtime.advance_instance(
            db, instance, payload.action, payload.note, notifier=notifier
        )
    except engine.InvalidTransitionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    db.commit()
    db.refresh(instance)
    return _detail(instance)


@router.post("/{instance_id}/compensate", response_model=WorkflowInstanceDetail)
def compensate(
    instance_id: uuid.UUID,
    payload: CompensateRequest,
    db: Session = Depends(get_db),
) -> WorkflowInstanceDetail:
    instance = _load_instance(db, instance_id)
    try:
        workflow_runtime.compensate_instance(
            db, instance, payload.note, notifier=notifier
        )
    except engine.InvalidTransitionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    db.commit()
    db.refresh(instance)
    return _detail(instance)
