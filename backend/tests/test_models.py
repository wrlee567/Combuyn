"""ORM-level tests: constraints, JSONB roundtrips, and column defaults."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.ccf import (
    DEFAULT_ORG_ID,
    CommonControl,
    Framework,
    FrameworkRequirement,
)
from app.models.vendor import Vendor


def test_vendor_default_lifecycle_is_sourcing(db_session):
    with db_session() as session:
        vendor = Vendor(name="Test Vendor")
        session.add(vendor)
        session.commit()
        session.refresh(vendor)
        assert vendor.lifecycle_status == "sourcing"


def test_vendor_jsonb_risk_breakdown_roundtrip(db_session):
    data = {"data_classification": {"value": "confidential", "severity": 3}}
    with db_session() as session:
        vendor = Vendor(name="Breakdown Vendor", risk_breakdown=data)
        session.add(vendor)
        session.commit()
        session.refresh(vendor)
        assert vendor.risk_breakdown == data


def test_vendor_jsonb_questionnaire_roundtrip(db_session):
    responses = {"mfa_enforced": True, "encryption_at_rest": False}
    with db_session() as session:
        vendor = Vendor(name="Questionnaire Vendor", questionnaire_responses=responses)
        session.add(vendor)
        session.commit()
        session.refresh(vendor)
        assert vendor.questionnaire_responses == responses


def test_framework_unique_key_constraint(db_session):
    with db_session() as session:
        session.add(Framework(key="dup_fw", name="Framework A", org_id=DEFAULT_ORG_ID))
        session.commit()
        session.add(Framework(key="dup_fw", name="Framework B", org_id=DEFAULT_ORG_ID))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_requirement_unique_citation_constraint(db_session):
    with db_session() as session:
        fw = Framework(key="cite_test_fw", name="Citation Test Framework")
        session.add(fw)
        session.flush()
        session.add(FrameworkRequirement(framework_id=fw.id, citation="CITE-001", title="First"))
        session.commit()
        session.add(FrameworkRequirement(framework_id=fw.id, citation="CITE-001", title="Dup"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_control_unique_key_constraint(db_session):
    with db_session() as session:
        session.add(CommonControl(key="CCF-TEST-001", name="Control A", org_id=DEFAULT_ORG_ID))
        session.commit()
        session.add(CommonControl(key="CCF-TEST-001", name="Control B", org_id=DEFAULT_ORG_ID))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
