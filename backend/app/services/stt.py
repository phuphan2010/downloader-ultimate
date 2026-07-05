"""Speech-to-Text service using faster-whisper with SRT output generation."""
import asyncio
from pathlib import Path
from typing import Dict, Any, Tuple
from faster_whisper import WhisperModel

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def format_timestamp(seconds: float) -> str:
    """Format seconds into SRT timestamp string format (HH:MM:SS,mmm)."""
    millis = int((seconds % 1) * 1000)
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


class STTService:
    """Whisper Speech-to-Text service using faster-whisper."""

    def __init__(self):
        self.model = None

    def load_model(self):
        if self.model is None:
            logger.info("loading_whisper_model", size=settings.WHISPER_MODEL_SIZE)
            device = settings.WHISPER_DEVICE if settings.WHISPER_DEVICE in ["cpu", "cuda"] else "cpu"
            compute_type = "int8" if device == "cpu" else "float16"
            self.model = WhisperModel(settings.WHISPER_MODEL_SIZE, device=device, compute_type=compute_type)

    async def transcribe_audio(
        self, audio_path: Path, language: str = "auto"
    ) -> Tuple[str, str, str]:
        """Transcribe audio WAV file to text and generate SRT content.

        Returns:
            Tuple[full_text, srt_content, detected_language]
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found at {audio_path}")

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._run_whisper, audio_path, language)

        detected_lang = result.get("language", "unknown")
        segments = result.get("segments", [])
        full_text = result.get("text", "").strip()

        # Build SRT content
        srt_lines = []
        for idx, seg in enumerate(segments, 1):
            start_str = format_timestamp(seg["start"])
            end_str = format_timestamp(seg["end"])
            text = seg["text"].strip()
            srt_lines.append(f"{idx}\n{start_str} --> {end_str}\n{text}\n")

        srt_content = "\n".join(srt_lines)
        return full_text, srt_content, detected_lang

    def _run_whisper(self, audio_path: Path, language: str) -> Dict[str, Any]:
        self.load_model()
        opts = {}
        if language and language != "auto":
            opts["language"] = language
        segments_gen, info = self.model.transcribe(str(audio_path), **opts)

        segments = []
        text_parts = []
        for seg in segments_gen:
            text_parts.append(seg.text)
            segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text
            })

        return {
            "language": info.language,
            "text": "".join(text_parts),
            "segments": segments
        }


stt_service = STTService()
