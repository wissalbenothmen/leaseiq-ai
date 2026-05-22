from __future__ import annotations
from functools import lru_cache
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

WEAK_SECRET_KEYS = {
    "change-me-in-production",
    "secret",
    "changeme",
    "password",
    "supersecret",
}


class Settings(BaseSettings):
    APP_NAME: str = "LeaseIQ AI"
    DEBUG: bool = False
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    RATE_LIMIT_PER_MINUTE: int = 60

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/leaseiq"
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4.1-mini-2025-04-14"

    # DeepInfra Whisper Large v3 — Phase A of the audit-pipeline recipe
    DEEPINFRA_API_KEY: str = ""
    DEEPINFRA_BASE_URL: str = "https://api.deepinfra.com/v1/openai"
    WHISPER_MODEL: str = "openai/whisper-large-v3"
    MOCK_WHISPER: bool = False

    AZURE_DI_ENDPOINT: str = ""
    AZURE_DI_KEY: str = ""
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER: str = "lease-documents"

    CLAUSE_RISK_HIGH_THRESHOLD: float = 70.0
    CLAUSE_RISK_MEDIUM_THRESHOLD: float = 40.0

    CRITICAL_DATE_ALERT_DAYS: list[int] = [7, 30, 60, 90]
    OBLIGATION_OVERDUE_ALERT_DAYS: int = 1

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        if v.lower() in WEAK_SECRET_KEYS:
            raise ValueError("SECRET_KEY is too weak — use a securely generated value")
        return v

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
