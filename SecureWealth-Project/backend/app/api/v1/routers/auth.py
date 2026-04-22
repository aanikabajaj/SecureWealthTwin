"""
SecureWealth Twin — Auth Router.
Modified to support 2-Step Verification (OTP) and Security Challenge (Password + Captcha).
"""

from __future__ import annotations

import uuid
import random
import string
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.db.database import get_db
from backend.app.middleware.auth_middleware import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)
from backend.app.models.user import User, UserRole
from backend.app.models.wealth_profile import WealthProfile
from backend.app.services.email_service import email_service

router   = APIRouter()
settings = get_settings()
pwd_ctx  = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email:     EmailStr
    password:  str     = Field(..., min_length=8)
    full_name: str | None = None
    phone:     str | None = None


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp_code: str


class ChallengeVerifyRequest(BaseModel):
    password: str
    captcha_answer: str
    expected_captcha: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token:  str | None = None
    refresh_token: str | None = None
    token_type:    str = "bearer"
    otp_required:  bool = False
    message:       str | None = None


class UserProfileResponse(BaseModel):
    id:           uuid.UUID
    email:        str
    full_name:    str | None
    phone:        str | None
    role:         UserRole
    kyc_status:   str
    is_verified:  bool
    last_login:   datetime | None = None
    active_devices_count: int = 1
    created_at:   datetime

    model_config = {"from_attributes": True}


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = None
    phone:     str | None = None
    aa_vua:    str | None = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash(password: str) -> str:
    return pwd_ctx.hash(password)

def _verify(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    stmt   = select(User).where(User.email == req.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=req.email,
        hashed_password=_hash(req.password),
        full_name=req.full_name,
        phone=req.phone,
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    profile = WealthProfile(user_id=user.id)
    db.add(profile)
    await db.flush()
    await db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    stmt   = select(User).where(User.email == req.email)
    result = await db.execute(stmt)
    user   = result.scalar_one_or_none()

    if not user or not _verify(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    otp = email_service.generate_otp()
    user.otp_code = otp
    user.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
    
    db.add(user)
    await db.commit()

    await email_service.send_otp_email(user.email, otp)

    return TokenResponse(
        otp_required=True,
        message="Verification code sent to your registered email."
    )


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(req: OTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    stmt   = select(User).where(User.email == req.email)
    result = await db.execute(stmt)
    user   = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.otp_code or user.otp_code != req.otp_code:
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    if datetime.now(timezone.utc) > user.otp_expiry.replace(tzinfo=timezone.utc):
        raise HTTPException(status_code=400, detail="Verification code expired")

    user.otp_code = None
    user.otp_expiry = None
    user.last_login = datetime.now(timezone.utc)
    user.active_devices_count = 1
    
    db.add(user)
    await db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/verify-challenge")
async def verify_challenge(
    req: ChallengeVerifyRequest, 
    current_user: User = Depends(get_current_user)
):
    if not _verify(req.password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    if req.captcha_answer.lower() != req.expected_captcha.lower():
        raise HTTPException(status_code=400, detail="Invalid captcha answer")
    
    return {"status": "success", "message": "Challenge verified"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(req.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")

    user_id = uuid.UUID(payload["sub"])
    stmt    = select(User).where(User.id == user_id)
    result  = await db.execute(stmt)
    user    = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/logout", status_code=200)
async def logout():
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserProfileResponse)
async def me(current_user: User = Depends(get_current_user)):
    return UserProfileResponse.model_validate(current_user)


@router.patch("/me", response_model=UserProfileResponse)
async def update_me(
    req: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if req.full_name is not None:
        current_user.full_name = req.full_name
    if req.phone is not None:
        current_user.phone = req.phone
    if req.aa_vua is not None:
        current_user.aa_vua = req.aa_vua

    db.add(current_user)
    await db.flush()
    await db.refresh(current_user)
    return UserProfileResponse.model_validate(current_user)
