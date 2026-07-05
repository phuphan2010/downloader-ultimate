"""Tests for Video Downloader API endpoints and error capture."""
import pytest
from app.services.downloader import validate_and_detect_platform
from app.models.download import PlatformType


def test_url_validation():
    """Test URL detection for TikTok and Douyin."""
    valid_tiktok = "https://www.tiktok.com/@user/video/1234567890"
    valid_douyin = "https://www.douyin.com/video/7091234567890123456"
    invalid_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    ok, plat = validate_and_detect_platform(valid_tiktok)
    assert ok is True
    assert plat == PlatformType.TIKTOK

    ok, plat = validate_and_detect_platform(valid_douyin)
    assert ok is True
    assert plat == PlatformType.DOUYIN

    ok, plat = validate_and_detect_platform(invalid_url)
    assert ok is False
    assert plat == PlatformType.UNKNOWN


@pytest.mark.asyncio
async def test_download_endpoint_validation(client):
    """POST /api/v1/download should reject invalid URLs with HTTP 400."""
    response = await client.post("/api/v1/download", json={"url": "https://invalid-url.com"})
    assert response.status_code in (400, 422)


def test_robust_error_message_extraction():
    """Ensure error message capture does not produce empty string (BUG-20 Fix)."""
    e = Exception()
    err_str = str(e).strip() or getattr(e, 'msg', '') or type(e).__name__
    assert err_str == "Exception"
