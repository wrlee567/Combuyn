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
from app.seed.ccf_reference import COMMON_CONTROLS, FRAMEWORKS, REQUIREMENTS


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
