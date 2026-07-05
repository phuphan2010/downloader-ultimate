"""Pytest configuration and shared fixtures for backend tests."""
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """Async HTTP test client wired to the FastAPI app.

    Uses ASGI transport so no real HTTP server is needed.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
