"""Authentication endpoints: register, login, current-user, password reset."""
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import get_current_user
from app.schemas.auth import (
    DevLinkResponse, ForgotPasswordRequest, ResetPasswordRequest, TokenResponse, UserLogin,
    UserOut, UserRegister,
)
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: UserRegister):
    return auth_service.register_user(payload)


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    token = auth_service.login_user(UserLogin(username=form_data.username, password=form_data.password))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password", response_model=DevLinkResponse)
def forgot_password(payload: ForgotPasswordRequest):
    return auth_service.forgot_password(payload)


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest):
    return auth_service.reset_password(payload)
