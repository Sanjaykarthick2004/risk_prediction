"""Registration, login, and password reset. Username + password only — no email.

Passwords are always bcrypt-hashed, never stored in plaintext. There is no real way to
"deliver" a reset link without an email/SMS provider, so it is logged and returned directly
in the API response — see the module docstring on DevLinkResponse.
"""
import logging
from datetime import timedelta

from fastapi import HTTPException

from app.config import settings
from app.core.security import create_access_token, generate_random_token, hash_password, verify_password
from app.database.mongodb import users_collection
from app.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest, UserLogin, UserRegister
from app.utils.helpers import utcnow

logger = logging.getLogger(__name__)


def _public_user(doc: dict) -> dict:
    return {"username": doc["username"], "role": doc["role"], "created_at": doc["created_at"]}


def register_user(payload: UserRegister) -> dict:
    if users_collection.find_one({"username": payload.username}):
        raise HTTPException(status_code=409, detail="Username already taken")

    doc = {
        "username": payload.username,
        "password_hash": hash_password(payload.password),
        "role": payload.role,
        "reset_token": None,
        "reset_token_expires": None,
        "created_at": utcnow(),
    }
    users_collection.insert_one(doc)
    return _public_user(doc)


def login_user(payload: UserLogin) -> str:
    user = users_collection.find_one({"username": payload.username})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return create_access_token(subject=user["username"], role=user["role"])


def forgot_password(payload: ForgotPasswordRequest) -> dict:
    user = users_collection.find_one({"username": payload.username})
    if not user:
        # Same response either way — don't reveal whether the username exists.
        return {
            "message": "If that username exists, a reset link has been generated.",
            "simulated": True, "dev_link": None,
        }

    token = generate_random_token()
    users_collection.update_one(
        {"username": payload.username},
        {"$set": {
            "reset_token": token,
            "reset_token_expires": utcnow() + timedelta(minutes=settings.reset_token_expire_minutes),
        }},
    )
    dev_link = f"{settings.frontend_url}/reset-password?token={token}"
    logger.info("[SIMULATED PASSWORD RESET] username=%s link=%s", payload.username, dev_link)
    return {
        "message": "If that username exists, a reset link has been generated.",
        "simulated": True, "dev_link": dev_link,
    }


def reset_password(payload: ResetPasswordRequest) -> dict:
    user = users_collection.find_one({"reset_token": payload.token})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or already-used reset link")
    if user.get("reset_token_expires") and utcnow() > user["reset_token_expires"]:
        raise HTTPException(status_code=400, detail="Reset link has expired. Request a new one.")

    users_collection.update_one(
        {"username": user["username"]},
        {"$set": {"password_hash": hash_password(payload.new_password)},
         "$unset": {"reset_token": "", "reset_token_expires": ""}},
    )
    return {"message": "Password has been reset. You can now log in with your new password."}
