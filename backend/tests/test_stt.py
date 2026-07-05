"""Tests for Audio Extraction and Timestamp Formatter."""
from app.services.stt import format_timestamp


def test_srt_timestamp_formatter():
    """Test seconds conversion to SRT timestamp HH:MM:SS,mmm format."""
    assert format_timestamp(0.0) == "00:00:00,000"
    assert format_timestamp(65.5) == "00:01:05,500"
    assert format_timestamp(3661.123) == "01:01:01,123"
