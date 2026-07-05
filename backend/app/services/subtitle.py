"""FFmpeg Subtitle Burn-in service."""
import asyncio
from pathlib import Path
from app.core.logging import get_logger
from app.models.subtitle import SubtitleStyle

logger = get_logger(__name__)


def hex_to_ass_color(hex_str: str) -> str:
    """Convert #RRGGBB hex color to FFmpeg ASS color format &H00BBGGRR."""
    hex_clean = hex_str.lstrip("#")
    if len(hex_clean) == 6:
        r, g, b = hex_clean[0:2], hex_clean[2:4], hex_clean[4:6]
        return f"&H00{b}{g}{r}"
    return "&H00FFFFFF"


class SubtitleBurnerService:
    """Service to hardcode/burn subtitles directly into video frames using FFmpeg."""

    @staticmethod
    async def burn_subtitles(
        video_path: Path, srt_path: Path, output_video_path: Path, style: SubtitleStyle
    ) -> Path:
        """Burn SRT file into video stream with custom styling."""
        if not video_path.exists():
            raise FileNotFoundError(f"Input video not found: {video_path}")
        if not srt_path.exists():
            raise FileNotFoundError(f"SRT subtitle file not found: {srt_path}")

        output_video_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare ASS style force_style string
        primary_color = hex_to_ass_color(style.font_color)
        outline_color = hex_to_ass_color(style.outline_color)

        alignment = "2"  # Bottom center
        if style.position == "top":
            alignment = "6"
        elif style.position == "center":
            alignment = "10"

        # Escape path for FFmpeg filter on Windows
        srt_path_str = str(srt_path).replace("\\", "/").replace(":", "\\:")

        force_style = (
            f"Fontname={style.font_name},"
            f"Fontsize={style.font_size},"
            f"PrimaryColour={primary_color},"
            f"OutlineColour={outline_color},"
            f"Alignment={alignment},"
            f"BorderStyle=1,Outline=2"
        )

        filter_arg = f"subtitles='{srt_path_str}':force_style='{force_style}'"

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", filter_arg,
            "-c:a", "copy",
            str(output_video_path)
        ]

        logger.info("subtitle_burn_start", video=str(video_path), srt=str(srt_path))

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            err_msg = stderr.decode()
            logger.error("ffmpeg_sub_burn_error", error=err_msg)
            raise RuntimeError(f"FFmpeg subtitle burn failed: {err_msg}")

        logger.info("subtitle_burn_success", target=str(output_video_path))
        return output_video_path


subtitle_burner_service = SubtitleBurnerService()
