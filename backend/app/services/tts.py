"""Text-to-Speech Service using gTTS and ElevenLabs."""
import asyncio
from pathlib import Path
from typing import Dict, List, Any
from gtts import gTTS
import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TTSService:
    """Service to generate speech audio files from text segments."""

    async def generate_segment_tts(
        self, text: str, output_path: Path, lang: str = "vi", provider: str = settings.TTS_PROVIDER
    ) -> Path:
        """Generate audio MP3 file from text string."""
        if not text.strip():
            raise ValueError("Empty text string provided for TTS.")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if provider == "elevenlabs" and settings.ELEVENLABS_API_KEY:
            try:
                await self._generate_elevenlabs(text, output_path)
            except Exception as e:
                logger.warning("elevenlabs_failed_fallback_gtts", error=str(e))
                await self._generate_gtts(text, output_path, lang)
        else:
            await self._generate_gtts(text, output_path, lang)

        return output_path

    async def _generate_gtts(self, text: str, output_path: Path, lang: str):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._run_gtts, text, output_path, lang)

    @staticmethod
    def _run_gtts(text: str, output_path: Path, lang: str):
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(str(output_path))

    async def _generate_elevenlabs(self, text: str, output_path: Path):
        url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"  # Default Voice ID
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": settings.ELEVENLABS_API_KEY
        }
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=data, headers=headers)
            resp.raise_for_status()
            output_path.write_bytes(resp.content)


tts_service = TTSService()
