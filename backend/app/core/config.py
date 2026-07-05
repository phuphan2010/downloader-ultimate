"""Application configuration using Pydantic Settings.

All settings are loaded from environment variables or a .env file.
"""
from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings object — instantiated once at import time."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "Downloader Ultimate"
    APP_ENV: str = "development"  # development | staging | production
    DEBUG: bool = True
    SECRET_KEY: str = "changeme-in-production-use-a-long-random-string"
    API_V1_PREFIX: str = "/api/v1"

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: object) -> List[str]:
        """Allow CORS_ORIGINS to be a comma-separated string in env."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v  # type: ignore[return-value]

    # ── Redis / Celery ───────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # ── Storage ──────────────────────────────────────────────────────────────
    STORAGE_BACKEND: str = "local"  # local | s3
    STORAGE_LOCAL_PATH: str = "/tmp/downloader"
    MAX_DISK_USAGE_PERCENT: float = 80.0

    # AWS S3 (only used when STORAGE_BACKEND=s3)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_REGION: str = "ap-southeast-1"

    # ── Job Settings ─────────────────────────────────────────────────────────
    JOB_TTL_HOURS: int = 24  # Hours before job files are cleaned up
    MAX_VIDEO_SIZE_MB: int = 100

    # ── Auth ─────────────────────────────────────────────────────────────────
    API_KEY_HEADER: str = "X-API-Key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Rate Limiting ────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 30

    # ── External Services ────────────────────────────────────────────────────
    SENTRY_DSN: str = ""  # Leave empty to disable Sentry
    DEEPL_API_KEY: str = ""
    GOOGLE_TRANSLATE_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""

    # ── Whisper ──────────────────────────────────────────────────────────────
    WHISPER_MODEL: str = "base"  # tiny | base | small | medium | large


# Singleton settings instance — import this everywhere
settings = Settings()
