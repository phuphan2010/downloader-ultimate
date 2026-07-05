"""Audio mixing and dubbing synchronization service using FFmpeg."""
import asyncio
from pathlib import Path
from typing import List, Dict
from app.core.logging import get_logger
from app.services.translator import parse_srt

logger = get_logger(__name__)


def parse_timestamp_seconds(ts_str: str) -> float:
    """Convert 'HH:MM:SS,mmm' into total seconds float."""
    h_m_s, ms = ts_str.split(",")
    h, m, s = map(int, h_m_s.split(":"))
    return h * 3600 + m * 60 + s + int(ms) / 1000.0


class DubbingService:
    """Mix original audio track with generated TTS tracks."""

    @staticmethod
    async def mix_dubbed_video(
        video_path: Path,
        tts_audio_path: Path,
        output_video_path: Path,
        original_volume: float = 0.2,
        mix_mode: str = "overlay"
    ) -> Path:
        """Mix TTS audio track over original video audio track."""
        if not video_path.exists():
            raise FileNotFoundError(f"Input video not found: {video_path}")
        if not tts_audio_path.exists():
            raise FileNotFoundError(f"TTS audio not found: {tts_audio_path}")

        output_video_path.parent.mkdir(parents=True, exist_ok=True)

        if mix_mode == "replace":
            # Completely replace original audio with TTS audio
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-i", str(tts_audio_path),
                "-c:v", "copy",
                "-c:a", "aac",
                "-map", "0:v:0",
                "-map", "1:a:0",
                str(output_video_path)
            ]
        else:
            # Overlay mode: lower original audio volume and mix with TTS audio
            filter_complex = f"[0:a]volume={original_volume}[aorig];[1:a]volume=1.0[atts];[aorig][atts]amix=inputs=2:duration=first[aout]"
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-i", str(tts_audio_path),
                "-filter_complex", filter_complex,
                "-map", "0:v:0",
                "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", "aac",
                str(output_video_path)
            ]

        logger.info("dubbing_mix_start", video=str(video_path), mix_mode=mix_mode)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            err_msg = stderr.decode()
            logger.error("ffmpeg_dub_mix_error", error=err_msg)
            raise RuntimeError(f"FFmpeg audio mix failed: {err_msg}")

        logger.info("dubbing_mix_success", target=str(output_video_path))
        return output_video_path


dubbing_service = DubbingService()
