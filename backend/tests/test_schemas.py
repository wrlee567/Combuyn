"""Pure Pydantic validation tests — no DB or HTTP fixtures needed."""

from __future__ import annotations

import types
import uuid

import pytest
from pydantic import ValidationError

from app.schemas.vendor import (
    QuestionnaireUpdate,
    VendorCreate,
    VendorSummary,
)


def test_vendor_create_rejects_empty_name():
    with pytest.raises(ValidationError):
        VendorCreate(name="")


def test_vendor_create_rejects_name_over_255():
    with pytest.raises(ValidationError):
        VendorCreate(name="x" * 256)


def test_vendor_create_defaults():
    v = VendorCreate(name="Valid Name")
    assert v.lifecycle_status == "sourcing"
    assert v.industry == "other"
    assert v.data_classification == "internal"
    assert v.network_connectivity == "limited"
    assert v.geography == "domestic"


def test_questionnaire_update_accepts_dict():
    u = QuestionnaireUpdate(responses={"mfa_enforced": True, "encryption_at_rest": False})
    assert u.responses["mfa_enforced"] is True
    assert u.responses["encryption_at_rest"] is False


def test_vendor_summary_from_orm():
    orm_obj = types.SimpleNamespace(
        id=uuid.uuid4(),
        name="Test Vendor",
        industry="technology",
        lifecycle_status="sourcing",
        inherent_risk_score=42,
        inherent_risk_tier="Medium",
    )
    summary = VendorSummary.model_validate(orm_obj)
    assert summary.name == "Test Vendor"
    assert summary.inherent_risk_tier == "Medium"
    assert summary.inherent_risk_score == 42
