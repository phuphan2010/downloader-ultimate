"""Security module for API key hashing and Redis persistence (BUG-04 & BUG-08 Fix)."""
import secrets
from typing import Dict, Optional, Tuple
import bcrypt

from app.core.config import settings
from app.services.redis_store import redis_store


def generate_api_key() -> Tuple[str, str]:
    """Generate a raw API Key and its bcrypt hash.

    Returns:
        Tuple[raw_key, hashed_key]
    """
    raw_key = f"dt_{secrets.token_urlsafe(32)}"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(raw_key.encode("utf-8"), salt).decode("utf-8")
    return raw_key, hashed


def save_key_to_store(hashed_key: str, key_data: Dict) -> None:
    redis_store.save_api_key(hashed_key, key_data)


def get_all_keys_from_store() -> Dict[str, Dict]:
    return redis_store.get_all_api_keys()


def verify_api_key(raw_key: str) -> bool:
    """Verify if raw API Key matches any valid key in Redis/Store (BUG-08: No hardcoded backdoor)."""
    if not raw_key:
        return False

    keys_db = get_all_keys_from_store()
    for hashed, metadata in keys_db.items():
        if metadata.get("is_active", True):
            try:
                if bcrypt.checkpw(raw_key.encode("utf-8"), hashed.encode("utf-8")):
                    return True
            except Exception:
                continue

    return False
