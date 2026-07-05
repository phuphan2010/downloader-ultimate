"""Tests for ASS color conversion."""
from app.services.subtitle import hex_to_ass_color


def test_hex_to_ass_color():
    """Test hex RRGGBB conversion to ASS &H00BBGGRR format."""
    assert hex_to_ass_color("#FFFFFF") == "&H00FFFFFF"
    assert hex_to_ass_color("#FF0000") == "&H000000FF"
    assert hex_to_ass_color("#00FF00") == "&H0000FF00"
    assert hex_to_ass_color("#0000FF") == "&H00FF0000"
