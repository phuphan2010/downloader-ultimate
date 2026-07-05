"""FastAPI Dependencies for API Security and Authentication."""
from fastapi import Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings
from app.core.security import verify_api_key
from app.services.redis_store import redis_store

api_key_header_scheme = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)


async def get_current_api_key(api_key: str = Security(api_key_header_scheme)) -> str:
    """Dependency to enforce valid API Key in X-API-Key header and rate limiting."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing required authentication header: {settings.API_KEY_HEADER}",
            headers={"WWW-Authenticate": "APIKey"},
        )

    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API Key.",
            headers={"WWW-Authenticate": "APIKey"},
        )

    # Check Rate Limit (BUG-14 Fix)
    if not redis_store.check_rate_limit(api_key, limit=settings.RATE_LIMIT_PER_MINUTE, window_sec=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {settings.RATE_LIMIT_PER_MINUTE} requests per minute.",
        )

    return api_key
