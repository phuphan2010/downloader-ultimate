"""FFmpeg Audio extraction and normalization service."""
import asyncio
from pathlib import Path
from app.core.logging import get_logger

logger = get_logger(__name__)


class AudioService:
    """Service to extract audio from video and normalize levels using FFmpeg."""

    @staticmethod
    async def extract_audio_wav(video_path: Path, output_wav_path: Path, normalize: bool = True) -> Path:
        """Extract audio to 16kHz mono WAV format (ideal for OpenAI Whisper)."""
        if not video_path.exists():
            raise FileNotFoundError(f"Input video file not found at {video_path}")

        output_wav_path.parent.mkdir(parents=True, exist_ok=True)

        if normalize:
            # Extract and apply loudnorm filter
            cmd = [
                "ffmpeg", "-y", "-i", str(video_path),
                "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                str(output_wav_path)
            ]
        else:
            cmd = [
                "ffmpeg", "-y", "-i", str(video_path),
                "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                str(output_wav_path)
            ]

        logger.info("extract_audio_start", video=str(video_path), target=str(output_wav_path))

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            err_msg = stderr.decode()
            logger.error("ffmpeg_extract_error", error=err_msg)
            raise RuntimeError(f"FFmpeg audio extraction failed: {err_msg}")

        if not output_wav_path.exists() or output_wav_path.stat().st_size == 0:
            raise RuntimeError("Extracted WAV file is empty or missing (video may not contain audio).")

        logger.info("extract_audio_success", target=str(output_wav_path))
        return output_wav_path


audio_service = AudioService()
