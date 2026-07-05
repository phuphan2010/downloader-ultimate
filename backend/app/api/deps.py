"""FastAPI Dependencies for API Security and Authentication."""
from fastapi import Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings
from app.core.security import verify_api_key

api_key_header_scheme = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)


async def get_current_api_key(api_key: str = Security(api_key_header_scheme)) -> str:
    """Dependency to enforce valid API Key in X-API-Key header."""
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

    return api_key
