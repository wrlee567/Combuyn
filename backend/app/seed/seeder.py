"""Idempotent seeding of the bundled CCF reference data."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ccf import (
    CommonControl,
    ControlRequirementMapping,
    Framework,
    FrameworkRequirement,
)
from app.models.vendor import Vendor
from app.models.workflow import WorkflowDefinition, WorkflowInstance
from app.seed.ccf_reference import COMMON_CONTROLS, FRAMEWORKS, REQUIREMENTS
from app.seed.vendors_reference import SAMPLE_VENDORS
from app.seed.workflow_reference import SAMPLE_INSTANCES, WORKFLOW_DEFINITIONS
from app.services import workflow_runtime
from app.services.risk_scoring import compute_inherent_risk
from app.services.workflow_engine import validate_blueprint


def seed_ccf(db: Session) -> dict[str, int]:
    """Populate frameworks, requirements, controls, and mappings.

    Idempotent: re-running only inserts what is missing, so it is safe to call
    on every startup. Returns counts of rows created.
    """
    created = {"frameworks": 0, "requirements": 0, "controls": 0, "mappings": 0}

    # Frameworks + their requirements.
    fw_by_key: dict[str, Framework] = {}
    for fw_data in FRAMEWORKS:
        fw = db.scalar(select(Framework).where(Framework.key == fw_data["key"]))
        if fw is None:
            fw = Framework(**fw_data)
            db.add(fw)
            db.flush()
            created["frameworks"] += 1
        fw_by_key[fw.key] = fw

        for citation, title, description in REQUIREMENTS.get(fw_data["key"], []):
            exists = db.scalar(
                select(FrameworkRequirement).where(
                    FrameworkRequirement.framework_id == fw.id,
                    FrameworkRequirement.citation == citation,
                )
            )
            if exists is None:
                db.add(
                    FrameworkRequirement(
                        framework_id=fw.id,
                        citation=citation,
                        title=title,
                        description=description,
                    )
                )
                created["requirements"] += 1
    db.flush()

    # Index requirements by (framework_key, citation) for mapping lookups.
    req_index: dict[tuple[str, str], FrameworkRequirement] = {}
    for fw in fw_by_key.values():
        for req in fw.requirements:
            req_index[(fw.key, req.citation)] = req

    # Common controls + mappings.
    for ctrl_data in COMMON_CONTROLS:
        ctrl = db.scalar(
            select(CommonControl).where(CommonControl.key == ctrl_data["key"])
        )
        if ctrl is None:
            ctrl = CommonControl(
                key=ctrl_data["key"],
                name=ctrl_data["name"],
                domain=ctrl_data["domain"],
                description=ctrl_data["description"],
            )
            db.add(ctrl)
            db.flush()
            created["controls"] += 1

        for fw_key, citation, rel_type in ctrl_data["maps"]:
            req = req_index.get((fw_key, citation))
            if req is None:
                continue  # reference data inconsistency; skip defensively
            exists = db.scalar(
                select(ControlRequirementMapping).where(
                    ControlRequirementMapping.control_id == ctrl.id,
                    ControlRequirementMapping.requirement_id == req.id,
                )
            )
            if exists is None:
                db.add(
                    ControlRequirementMapping(
                        control_id=ctrl.id,
                        requirement_id=req.id,
                        relationship_type=rel_type,
                    )
                )
                created["mappings"] += 1

    db.commit()
    return created


def seed_vendors(db: Session) -> int:
    """Insert sample vendors (idempotent by name). Returns rows created."""
    created = 0
    for data in SAMPLE_VENDORS:
        exists = db.scalar(select(Vendor).where(Vendor.name == data["name"]))
        if exists is not None:
            continue
        vendor = Vendor(**data)
        result = compute_inherent_risk(
            data_classification=vendor.data_classification,
            network_connectivity=vendor.network_connectivity,
            industry=vendor.industry,
            geography=vendor.geography,
        )
        vendor.inherent_risk_score = result.score
        vendor.inherent_risk_tier = result.tier
        vendor.risk_breakdown = result.breakdown
        db.add(vendor)
        created += 1
    db.commit()
    return created


def seed_workflows(db: Session) -> dict[str, int]:
    """Insert workflow definitions and drive sample instances through them.

    Idempotent: definitions are keyed by ``key`` and instances by ``subject``.
    Sample instances are advanced via the real engine (notifications suppressed)
    so their persisted state and event log always match the live rules.
    Returns counts of rows created.
    """
    created = {"definitions": 0, "instances": 0}

    def_by_key: dict[str, WorkflowDefinition] = {}
    for data in WORKFLOW_DEFINITIONS:
        validate_blueprint(data["blueprint"])
        definition = db.scalar(
            select(WorkflowDefinition).where(WorkflowDefinition.key == data["key"])
        )
        if definition is None:
            definition = WorkflowDefinition(
                key=data["key"],
                name=data["name"],
                description=data["description"],
                blueprint=data["blueprint"],
            )
            db.add(definition)
            db.flush()
            created["definitions"] += 1
        def_by_key[definition.key] = definition

    for sample in SAMPLE_INSTANCES:
        exists = db.scalar(
            select(WorkflowInstance).where(
                WorkflowInstance.subject == sample["subject"]
            )
        )
        if exists is not None:
            continue
        definition = def_by_key[sample["definition_key"]]
        instance = workflow_runtime.start_instance(
            db, definition, sample["subject"], sample.get("context", {})
        )
        for action in sample.get("actions", []):
            workflow_runtime.advance_instance(db, instance, action)
        created["instances"] += 1

    db.commit()
    return created
