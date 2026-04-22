"""
SecureWealth Twin — Application Settings.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────────────────
    ENVIRONMENT: Literal["development", "production"] = "development"
    DEBUG: bool = True
    APP_NAME: str = "SecureWealth Twin"
    APP_VERSION: str = "1.0.0"

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/securewealth"
    USE_SQLITE: bool = True
    SQLITE_URL: str = "sqlite+aiosqlite:///./securewealth_dev.db"

    # ── Auth / JWT ────────────────────────────────────────────────────────
    SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION-USE-OPENSSL-RAND-HEX-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── SMTP (Email Delivery) ──────────────────────────────────────────────
    # To use real Gmail delivery, set these in your .env file
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "aanikabajaj290@gmail.com"
    SMTP_PASSWORD: str = "" # ENTER YOUR APP PASSWORD HERE
    EMAIL_FROM: str = "aanikabajaj290@gmail.com"

    # ── AI Service Bridge ─────────────────────────────────────────────────
    AI_SERVICE_URL: str = "http://localhost:8001"

    @property
    def allowed_origins_list(self) -> list[str]:
        return ["http://localhost:3000", "http://localhost:5173"]

    @property
    def effective_db_url(self) -> str:
        return self.SQLITE_URL if self.USE_SQLITE else self.DATABASE_URL


@lru_cache
def get_settings() -> Settings:
    return Settings()
