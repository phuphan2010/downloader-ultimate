"""Tests for image validation."""
from pathlib import Path
from app.services.logo import validate_image_file


def test_invalid_image_validation(tmp_path):
    """Non-image files should be rejected."""
    fake_img = tmp_path / "fake.png"
    fake_img.write_text("NOT AN IMAGE CONTENT")

    assert validate_image_file(fake_img) is False
