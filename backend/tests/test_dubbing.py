"""Tests for Timestamp Parser."""
from app.services.dubbing import parse_timestamp_seconds


def test_parse_timestamp_seconds():
    """Test converting timestamp strings to float seconds."""
    assert parse_timestamp_seconds("00:00:05,500") == 5.5
    assert parse_timestamp_seconds("00:01:00,000") == 60.0
    assert parse_timestamp_seconds("01:00:00,000") == 3600.0
