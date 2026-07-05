"""Tests for SRT Parsing, Translation service and VTT conversion."""
from app.services.translator import parse_srt, build_srt, convert_srt_to_vtt

SAMPLE_SRT = """1
00:00:01,000 --> 00:00:03,500
Hello world

2
00:00:04,000 --> 00:00:06,000
Testing translation
"""


def test_srt_parser_and_builder():
    """Test parsing SRT to dicts and rebuilding SRT."""
    parsed = parse_srt(SAMPLE_SRT)
    assert len(parsed) == 2
    assert parsed[0]["text"] == "Hello world"
    assert parsed[1]["timestamp"] == "00:00:04,000 --> 00:00:06,000"

    rebuilt = build_srt(parsed)
    assert "Hello world" in rebuilt
    assert "00:00:04,000 --> 00:00:06,000" in rebuilt


def test_vtt_conversion():
    """Test SRT to WebVTT conversion."""
    vtt = convert_srt_to_vtt(SAMPLE_SRT)
    assert vtt.startswith("WEBVTT")
    assert "00:00:01.000 --> 00:00:03.500" in vtt
