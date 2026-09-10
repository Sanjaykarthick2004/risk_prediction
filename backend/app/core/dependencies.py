"""FastAPI dependencies: current authenticated user."""
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.database.mongodb import users_collection

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    username = payload.get("sub")
    user = users_collection.find_one(
        {"username": username},
        {"_id": 0, "password_hash": 0, "reset_token": 0, "reset_token_expires": 0},
    )
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
