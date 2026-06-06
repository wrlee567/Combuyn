"""Pydantic response/request schemas for the CCF API."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class FrameworkOut(ORMModel):
    id: uuid.UUID
    key: str
    name: str
    version: str
    authority: str
    description: str
    category: str
    requirement_count: int = 0


class RequirementOut(ORMModel):
    id: uuid.UUID
    citation: str
    title: str
    description: str


class FrameworkRequirementRef(BaseModel):
    """A requirement plus its parent framework, for the coverage matrix."""

    framework_key: str
    framework_name: str
    citation: str
    title: str
    relationship_type: str


class ControlOut(ORMModel):
    id: uuid.UUID
    key: str
    name: str
    domain: str
    description: str


class ControlCoverageOut(BaseModel):
    """A common control with every framework requirement it satisfies."""

    id: uuid.UUID
    key: str
    name: str
    domain: str
    description: str
    frameworks_covered: list[str]
    requirements: list[FrameworkRequirementRef]


class CoverageSummary(BaseModel):
    """Top-level numbers for the dashboard."""

    frameworks: int
    requirements: int
    common_controls: int
    mappings: int
