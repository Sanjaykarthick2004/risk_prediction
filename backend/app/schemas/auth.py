"""Pydantic schemas for authentication (username + password only — no email)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    role: str = Field("RESEARCHER", pattern="^(ADMIN|RESEARCHER)$")


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    username: str
    role: str
    created_at: datetime


class ForgotPasswordRequest(BaseModel):
    username: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6, max_length=128)


class DevLinkResponse(BaseModel):
    """No real email/SMS exists to deliver this to, so the reset link is logged to
    backend/logs/app.log AND returned here so the flow can be exercised directly in the UI —
    a deliberate college-project shortcut, not something a production system would do.
    """
    message: str
    simulated: bool = True
    dev_link: Optional[str] = None
