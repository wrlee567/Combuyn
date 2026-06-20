"""Pydantic schemas for the Workflow Orchestration API — Iteration 3."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class WorkflowDefinitionSummary(ORMModel):
    id: uuid.UUID
    key: str
    name: str
    description: str


class WorkflowDefinitionDetail(WorkflowDefinitionSummary):
    blueprint: dict


class TransitionOption(BaseModel):
    action: str
    target: str
    compensation: str = ""


class WorkflowEventOut(ORMModel):
    sequence: int
    kind: str
    action: str
    from_state: str
    to_state: str
    note: str


class WorkflowInstanceSummary(ORMModel):
    id: uuid.UUID
    definition_id: uuid.UUID
    subject: str
    current_state: str
    status: str


class WorkflowInstanceDetail(WorkflowInstanceSummary):
    definition_key: str
    definition_name: str
    context: dict
    blueprint: dict
    events: list[WorkflowEventOut]
    available_actions: list[TransitionOption]


class InstanceCreate(BaseModel):
    definition_key: str = Field(min_length=1)
    subject: str = Field(min_length=1, max_length=255)
    context: dict = Field(default_factory=dict)


class AdvanceRequest(BaseModel):
    action: str = Field(min_length=1)
    note: str = ""


class CompensateRequest(BaseModel):
    note: str = ""
