"""Pydantic schemas for the login flow."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    org_id: uuid.UUID
