"""Pytest configuration and shared fixtures with test API key setup."""
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.security import generate_api_key, save_key_to_store

TEST_API_KEY = "dt_test_key_1234567890"


@pytest.fixture(autouse=True)
def setup_test_api_key():
    """Register test API key automatically for test execution."""
    save_key_to_store(
        TEST_API_KEY,
        {"key_id": "test-key-id", "name": "Test Key", "is_active": True}
    )


@pytest.fixture
async def client() -> AsyncClient:
    """Async HTTP client for testing FastAPI endpoints with X-API-Key header."""
    headers = {"X-API-Key": TEST_API_KEY}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", headers=headers
    ) as ac:
        yield ac
