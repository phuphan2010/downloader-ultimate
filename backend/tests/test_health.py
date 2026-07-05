"""Tests for the health check endpoint."""
import pytest


@pytest.mark.asyncio
async def test_health_check_returns_200(client):
    """Health check should always return 200."""
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_check_response_schema(client):
    """Health check response should have required fields."""
    response = await client.get("/health")
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "services" in data
    assert data["status"] in ("ok", "degraded")
