"""FFmpeg Logo Overlay service with image magic bytes validation."""
import asyncio
from pathlib import Path
from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)

# Magic bytes signature for PNG, JPEG, WEBP
IMAGE_SIGNATURES = {
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpeg",
    b"RIFF": "webp",
}


def validate_image_file(file_path: Path) -> bool:
    """Validate image file extension and magic bytes header."""
    if not file_path.exists() or file_path.stat().st_size == 0:
        return False

    with open(file_path, "rb") as f:
        header = f.read(12)

    for sig in IMAGE_SIGNATURES:
        if header.startswith(sig):
            return True
    return False


class LogoOverlayService:
    """Service to overlay watermark/logo image on top of video stream."""

    @staticmethod
    async def overlay_logo(
        video_path: Path,
        logo_path: Path,
        output_video_path: Path,
        position: str = "top-right",
        size_percent: int = 15,
        opacity: float = 0.8,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> Path:
        """Apply logo overlay filter via FFmpeg."""
        if not video_path.exists():
            raise FileNotFoundError(f"Input video not found: {video_path}")
        if not validate_image_file(logo_path):
            raise ValueError(f"Invalid logo file or unsupported image format: {logo_path}")

        output_video_path.parent.mkdir(parents=True, exist_ok=True)

        # Position calculation
        pos_expr = "main_w-overlay_w-10:10"  # top-right default
        if position == "top-left":
            pos_expr = "10:10"
        elif position == "bottom-left":
            pos_expr = "10:main_h-overlay_h-10"
        elif position == "bottom-right":
            pos_expr = "main_w-overlay_w-10:main_h-overlay_h-10"
        elif position == "center":
            pos_expr = "(main_w-overlay_w)/2:(main_h-overlay_h)/2"

        # Enable timeline expression
        enable_expr = ""
        if start_time is not None and end_time is not None:
            enable_expr = f":enable='between(t,{start_time},{end_time})'"
        elif start_time is not None:
            enable_expr = f":enable='gte(t,{start_time})'"

        filter_complex = (
            f"[1:v]scale=iw*{size_percent}/100:-1,format=rgba,colorchannelmixer=aa={opacity}[logo];"
            f"[0:v][logo]overlay={pos_expr}{enable_expr}[vout]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(logo_path),
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-c:a", "copy",
            str(output_video_path)
        ]

        logger.info("logo_overlay_start", video=str(video_path), logo=str(logo_path))

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            err_msg = stderr.decode()
            logger.error("ffmpeg_logo_error", error=err_msg)
            raise RuntimeError(f"FFmpeg logo overlay failed: {err_msg}")

        logger.info("logo_overlay_success", target=str(output_video_path))
        return output_video_path


logo_service = LogoOverlayService()
