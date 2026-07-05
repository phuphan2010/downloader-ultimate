"""Main FastAPI application entry point."""
import shutil
from typing import Any, Dict

import redis as redis_client
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.middleware import RequestIDMiddleware

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Downloader Ultimate API",
    description="Video Downloader & Dubbing Tool — REST API\n\nSupports TikTok/Douyin download, STT, translation, TTS dubbing, subtitle burn-in, and logo overlay.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"], summary="Health check")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint — public, no auth required.

    Checks:
    - API server: always OK if endpoint responds
    - Redis: ping test
    - Disk space: warn if > configured threshold
    """
    health: Dict[str, Any] = {
        "status": "ok",
        "version": "0.1.0",
        "services": {},
    }

    # Check Redis
    try:
        r = redis_client.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        health["services"]["redis"] = "ok"
    except Exception as e:
        health["services"]["redis"] = f"error: {str(e)}"
        health["status"] = "degraded"

    # Check disk space
    try:
        disk = shutil.disk_usage(
            settings.STORAGE_LOCAL_PATH
            if settings.STORAGE_BACKEND == "local"
            else "/"
        )
        disk_percent = (disk.used / disk.total) * 100
        health["services"]["disk"] = {
            "used_percent": round(disk_percent, 1),
            "free_gb": round(disk.free / (1024**3), 2),
        }
        if disk_percent > settings.MAX_DISK_USAGE_PERCENT:
            health["services"]["disk"]["warning"] = "disk usage critical"
            health["status"] = "degraded"
    except Exception as e:
        health["services"]["disk"] = f"error: {str(e)}"

    logger.info("health_check", **health)
    return health
