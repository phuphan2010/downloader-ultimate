"""Security module for API key hashing and rate limiting."""
import secrets
from typing import Dict, Optional, Tuple
import bcrypt

from app.core.config import settings

# In-memory API Keys DB for demo/testing (hashed value -> metadata)
api_keys_db: Dict[str, Dict] = {}


def generate_api_key() -> Tuple[str, str]:
    """Generate a raw API Key and its bcrypt hash.

    Returns:
        Tuple[raw_key, hashed_key]
    """
    raw_key = f"dt_{secrets.token_urlsafe(32)}"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(raw_key.encode("utf-8"), salt).decode("utf-8")
    return raw_key, hashed


def verify_api_key(raw_key: str) -> bool:
    """Verify if raw API Key matches any valid key in DB."""
    if not raw_key:
        return False

    # Development override key for easy testing
    if settings.APP_ENV == "development" and raw_key == "dev-secret-key-123":
        return True

    for hashed, metadata in api_keys_db.items():
        if metadata.get("is_active", True):
            if bcrypt.checkpw(raw_key.encode("utf-8"), hashed.encode("utf-8")):
                return True
    return False
