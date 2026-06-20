"""JWT bearer authentication and tenant resolution.

Every authenticated request carries a signed JWT whose ``org_id`` claim scopes
all data access to a single tenant. The :func:`current_org` dependency decodes
the token and returns the caller's org id; routers use it to filter queries so
one tenant can never read or write another tenant's rows.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

settings = get_settings()

# auto_error=False so we can raise a 401 with a WWW-Authenticate header instead
# of FastAPI's default 403 for a missing credential.
_bearer = HTTPBearer(auto_error=False)


def create_access_token(
    org_id: uuid.UUID, subject: str = "user", expires_in: timedelta | None = None
) -> str:
    """Mint a JWT for the given tenant. Used by tests and future login flows."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "org_id": str(org_id),
        "iat": now,
        "exp": now + (expires_in or timedelta(hours=12)),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def hash_password(password: str) -> str:
    """Hash a password with PBKDF2-SHA256 and a random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return f"{salt}:{key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Return True if password matches the stored PBKDF2 hash."""
    try:
        salt, key_hex = stored_hash.split(":", 1)
    except ValueError:
        return False
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return secrets.compare_digest(key.hex(), key_hex)


def current_org(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> uuid.UUID:
    """Resolve the caller's tenant from a bearer token, or raise 401."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid bearer token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or not credentials.credentials:
        raise unauthorized
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return uuid.UUID(str(payload["org_id"]))
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise unauthorized from exc
