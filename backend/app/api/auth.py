"""Demo-only authentication helpers."""

from fastapi import APIRouter, HTTPException

from app.auth import create_access_token
from app.config import get_settings
from app.models.ccf import DEFAULT_ORG_ID

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/demo-token")
def demo_token() -> dict[str, str]:
    """Mint a default-tenant JWT for portfolio demos only."""
    if not get_settings().enable_demo_auth:
        raise HTTPException(status_code=404, detail="Not found")

    return {
        "access_token": create_access_token(DEFAULT_ORG_ID),
        "token_type": "bearer",
    }
