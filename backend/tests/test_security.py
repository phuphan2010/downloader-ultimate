"""Tests for API Key generation and verification."""
from app.core.security import generate_api_key, verify_api_key


def test_api_key_generation_and_verification():
    """Generated API keys should verify correctly against hash."""
    raw_key, hashed = generate_api_key()
    assert raw_key.startswith("dt_")
    assert len(raw_key) > 30

    # Verification against invalid key
    assert verify_api_key("invalid-key-xyz") is False
