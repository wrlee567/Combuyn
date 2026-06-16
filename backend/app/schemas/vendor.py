"""Pydantic schemas for the TPRM Vendor API."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class VendorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    contact_name: str = ""
    contact_email: str = ""
    description: str = ""
    industry: str = "other"
    data_classification: str = "internal"
    network_connectivity: str = "limited"
    geography: str = "domestic"
    lifecycle_status: str = "sourcing"


class VendorSummary(ORMModel):
    id: uuid.UUID
    name: str
    industry: str
    lifecycle_status: str
    inherent_risk_score: int
    inherent_risk_tier: str


class VendorDetail(ORMModel):
    id: uuid.UUID
    name: str
    contact_name: str
    contact_email: str
    description: str
    industry: str
    data_classification: str
    network_connectivity: str
    geography: str
    lifecycle_status: str
    inherent_risk_score: int
    inherent_risk_tier: str
    risk_breakdown: dict
    questionnaire_responses: dict


class QuestionnaireUpdate(BaseModel):
    responses: dict


class LifecycleUpdate(BaseModel):
    lifecycle_status: str
