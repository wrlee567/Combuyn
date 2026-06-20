"""TPRM Vendor API — Iteration 2.

Create vendors (inherent risk is computed at intake), list/inspect them, advance
them through the lifecycle, and capture dynamic questionnaire responses.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.vendor import LIFECYCLE_PHASES, Vendor
from app.schemas.vendor import (
    LifecycleUpdate,
    QuestionnaireUpdate,
    VendorCreate,
    VendorDetail,
    VendorSummary,
)
from app.seed.questionnaire import (
    QUESTIONNAIRE_TEMPLATE,
    QUESTIONNAIRE_VERSION,
    validate_responses,
)
from app.services.risk_scoring import (
    InvalidFactorError,
    compute_inherent_risk,
    factor_options,
)

router = APIRouter(prefix="/api/vendors", tags=["vendors"])


def _apply_inherent_risk(vendor: Vendor) -> None:
    """(Re)compute and store inherent risk from the vendor's factors."""
    try:
        result = compute_inherent_risk(
            data_classification=vendor.data_classification,
            network_connectivity=vendor.network_connectivity,
            industry=vendor.industry,
            geography=vendor.geography,
        )
    except InvalidFactorError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    vendor.inherent_risk_score = result.score
    vendor.inherent_risk_tier = result.tier
    vendor.risk_breakdown = result.breakdown


# Static metadata endpoints — placed before /{vendor_id} so they aren't
# captured by the UUID path param.
@router.get("/options")
def options() -> dict:
    """Allowed factor values + lifecycle phases to drive the intake form."""
    return {"factors": factor_options(), "lifecycle_phases": LIFECYCLE_PHASES}


@router.get("/questionnaire-template")
def questionnaire_template() -> dict:
    return {"version": QUESTIONNAIRE_VERSION, "sections": QUESTIONNAIRE_TEMPLATE}


@router.get("", response_model=list[VendorSummary])
def list_vendors(db: Session = Depends(get_db)) -> list[VendorSummary]:
    stmt = select(Vendor).order_by(Vendor.inherent_risk_score.desc(), Vendor.name)
    return [VendorSummary.model_validate(v) for v in db.scalars(stmt)]


@router.post("", response_model=VendorDetail, status_code=201)
def create_vendor(payload: VendorCreate, db: Session = Depends(get_db)) -> VendorDetail:
    if payload.lifecycle_status not in LIFECYCLE_PHASES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid lifecycle_status. Allowed: {', '.join(LIFECYCLE_PHASES)}.",
        )
    vendor = Vendor(**payload.model_dump())
    _apply_inherent_risk(vendor)
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return VendorDetail.model_validate(vendor)


@router.get("/{vendor_id}", response_model=VendorDetail)
def get_vendor(vendor_id: uuid.UUID, db: Session = Depends(get_db)) -> VendorDetail:
    vendor = db.get(Vendor, vendor_id)
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return VendorDetail.model_validate(vendor)


@router.patch("/{vendor_id}/questionnaire", response_model=VendorDetail)
def update_questionnaire(
    vendor_id: uuid.UUID,
    payload: QuestionnaireUpdate,
    db: Session = Depends(get_db),
) -> VendorDetail:
    vendor = db.get(Vendor, vendor_id)
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")

    errors = validate_responses(payload.responses)
    if errors:
        raise HTTPException(status_code=422, detail="; ".join(errors))

    # Merge so partial saves don't wipe prior answers.
    merged = {**vendor.questionnaire_responses, **payload.responses}
    vendor.questionnaire_responses = merged
    db.commit()
    db.refresh(vendor)
    return VendorDetail.model_validate(vendor)


@router.patch("/{vendor_id}/lifecycle", response_model=VendorDetail)
def update_lifecycle(
    vendor_id: uuid.UUID,
    payload: LifecycleUpdate,
    db: Session = Depends(get_db),
) -> VendorDetail:
    if payload.lifecycle_status not in LIFECYCLE_PHASES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid lifecycle_status. Allowed: {', '.join(LIFECYCLE_PHASES)}.",
        )
    vendor = db.get(Vendor, vendor_id)
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")
    vendor.lifecycle_status = payload.lifecycle_status
    db.commit()
    db.refresh(vendor)
    return VendorDetail.model_validate(vendor)
