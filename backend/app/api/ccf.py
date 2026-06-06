"""CCF API — frameworks, controls, and the control-coverage matrix."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.ccf import (
    CommonControl,
    ControlRequirementMapping,
    Framework,
    FrameworkRequirement,
)
from app.schemas.ccf import (
    ControlCoverageOut,
    ControlOut,
    CoverageSummary,
    FrameworkOut,
    FrameworkRequirementRef,
    RequirementOut,
)

router = APIRouter(prefix="/api", tags=["ccf"])


@router.get("/summary", response_model=CoverageSummary)
def summary(db: Session = Depends(get_db)) -> CoverageSummary:
    """Top-level counts for the dashboard."""
    return CoverageSummary(
        frameworks=db.scalar(select(func.count(Framework.id))) or 0,
        requirements=db.scalar(select(func.count(FrameworkRequirement.id))) or 0,
        common_controls=db.scalar(select(func.count(CommonControl.id))) or 0,
        mappings=db.scalar(select(func.count(ControlRequirementMapping.id))) or 0,
    )


@router.get("/frameworks", response_model=list[FrameworkOut])
def list_frameworks(
    category: str | None = None, db: Session = Depends(get_db)
) -> list[FrameworkOut]:
    """List frameworks, optionally filtered by category (enterprise/medical)."""
    stmt = select(Framework).options(selectinload(Framework.requirements))
    if category:
        stmt = stmt.where(Framework.category == category)
    stmt = stmt.order_by(Framework.name)

    out: list[FrameworkOut] = []
    for fw in db.scalars(stmt):
        model = FrameworkOut.model_validate(fw)
        model.requirement_count = len(fw.requirements)
        out.append(model)
    return out


@router.get("/frameworks/{framework_id}/requirements", response_model=list[RequirementOut])
def list_requirements(
    framework_id: uuid.UUID, db: Session = Depends(get_db)
) -> list[RequirementOut]:
    """List the requirements/citations for a framework."""
    fw = db.get(Framework, framework_id)
    if fw is None:
        raise HTTPException(status_code=404, detail="Framework not found")
    stmt = (
        select(FrameworkRequirement)
        .where(FrameworkRequirement.framework_id == framework_id)
        .order_by(FrameworkRequirement.citation)
    )
    return [RequirementOut.model_validate(r) for r in db.scalars(stmt)]


@router.get("/controls", response_model=list[ControlOut])
def list_controls(db: Session = Depends(get_db)) -> list[ControlOut]:
    """List common controls."""
    stmt = select(CommonControl).order_by(CommonControl.key)
    return [ControlOut.model_validate(c) for c in db.scalars(stmt)]


@router.get("/coverage", response_model=list[ControlCoverageOut])
def control_coverage(db: Session = Depends(get_db)) -> list[ControlCoverageOut]:
    """The heart of the CCF: each common control with every framework
    requirement it satisfies. This is what proves 'implement once, comply many'.
    """
    stmt = (
        select(CommonControl)
        .options(
            selectinload(CommonControl.mappings)
            .selectinload(ControlRequirementMapping.requirement)
            .selectinload(FrameworkRequirement.framework)
        )
        .order_by(CommonControl.key)
    )

    out: list[ControlCoverageOut] = []
    for ctrl in db.scalars(stmt):
        refs: list[FrameworkRequirementRef] = []
        frameworks_covered: set[str] = set()
        for mapping in ctrl.mappings:
            req = mapping.requirement
            fw = req.framework
            frameworks_covered.add(fw.name)
            refs.append(
                FrameworkRequirementRef(
                    framework_key=fw.key,
                    framework_name=fw.name,
                    citation=req.citation,
                    title=req.title,
                    relationship_type=mapping.relationship_type,
                )
            )
        refs.sort(key=lambda r: (r.framework_name, r.citation))
        out.append(
            ControlCoverageOut(
                id=ctrl.id,
                key=ctrl.key,
                name=ctrl.name,
                domain=ctrl.domain,
                description=ctrl.description,
                frameworks_covered=sorted(frameworks_covered),
                requirements=refs,
            )
        )
    return out
