"""Application configuration using Pydantic Settings."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Application
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "*"]

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Storage
    STORAGE_BACKEND: str = "local"  # local | s3
    STORAGE_LOCAL_PATH: str = "/data/jobs"
    FILE_TTL_HOURS: int = 24
    MAX_DISK_USAGE_PERCENT: float = 80.0

    # AWS S3 (optional)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_REGION: str = "ap-southeast-1"

    # Download & Proxy Configuration
    MAX_VIDEO_SIZE_MB: int = 100
    DOWNLOAD_TIMEOUT_SEC: int = 300
    DOWNLOAD_RETRY_COUNT: int = 3
    COOKIES_FILE: str = "/app/cookies/cookies.txt"
    PROXY_URL: str = ""  # e.g. "http://proxy.example.com:8080"
    DOUYIN_API_SERVICE_URL: str = "http://192.168.1.200:8000"  # Host proxy IP or service URL
    DOUYIN_API_KEY: str = ""  # API key for douyin_tiktok_api proxy
    DOUYIN_API_DOWNLOAD_ENDPOINT: str = "/api/hybrid/video_data"  # Official endpoint for Douyin API V4

    # STT (Whisper)
    WHISPER_MODEL_SIZE: str = "base"  # tiny | base | small | medium | large
    WHISPER_DEVICE: str = "cpu"  # cpu | cuda

    # Translation
    TRANSLATE_PROVIDER: str = "google"  # google | deepl
    GOOGLE_TRANSLATE_API_KEY: str = ""
    DEEPL_API_KEY: str = ""

    # TTS
    TTS_PROVIDER: str = "gtts"  # gtts | elevenlabs
    ELEVENLABS_API_KEY: str = ""

    # Security / Auth
    API_KEY_HEADER: str = "X-API-Key"
    RATE_LIMIT_PER_MINUTE: int = 10
    RATE_LIMIT_PER_HOUR: int = 100

    # Sentry (optional)
    SENTRY_DSN: str = ""


settings = Settings()
