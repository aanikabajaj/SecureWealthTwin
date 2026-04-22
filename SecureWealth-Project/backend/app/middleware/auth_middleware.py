"""
SecureWealth Twin — Auth Middleware & JWT Dependency.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.database import get_db
from app.models.user import User

settings  = get_settings()
_bearer   = HTTPBearer(auto_error=True)

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


# ── Token helpers ─────────────────────────────────────────────────────────────

def create_access_token(user_id: uuid.UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "access"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_refresh_token(user_id: uuid.UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "refresh"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise CREDENTIALS_EXCEPTION


# ── FastAPI dependencies ───────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise CREDENTIALS_EXCEPTION

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise CREDENTIALS_EXCEPTION

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise CREDENTIALS_EXCEPTION

    stmt   = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user   = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise CREDENTIALS_EXCEPTION

    return user


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    from app.models.user import UserRole
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
