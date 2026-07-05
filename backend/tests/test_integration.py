"""Integration tests verifying full API Router registration and Health Endpoint."""
import pytest


@pytest.mark.asyncio
async def test_full_router_registration(client):
    """Verify OpenAPI schema generates and registers all endpoint paths."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    paths = schema.get("paths", {})

    assert "/health" in paths
    assert "/api/v1/download" in paths
    assert "/api/v1/jobs" in paths
    assert "/api/v1/transcribe" in paths
    assert "/api/v1/translate" in paths
    assert "/api/v1/subtitle" in paths
    assert "/api/v1/dub" in paths
    assert "/api/v1/logo" in paths
    assert "/api/v1/pipeline" in paths
    assert "/api/v1/admin/keys" in paths
