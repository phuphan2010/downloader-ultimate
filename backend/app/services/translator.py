"""Translation service supporting Google Translate and DeepL providers with SRT parsing and caching."""
import hashlib
import re
from typing import Dict, List, Tuple
from deep_translator import GoogleTranslator
import deepl

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

translation_cache: Dict[str, str] = {}


def parse_srt(srt_content: str) -> List[Dict[str, str]]:
    """Parse SRT string into structured list of blocks."""
    blocks = srt_content.strip().split("\n\n")
    parsed = []
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            index = lines[0]
            timestamp = lines[1]
            text = "\n".join(lines[2:])
            parsed.append({"index": index, "timestamp": timestamp, "text": text})
    return parsed


def build_srt(segments: List[Dict[str, str]]) -> str:
    """Build SRT format string from segments."""
    blocks = []
    for seg in segments:
        blocks.append(f"{seg['index']}\n{seg['timestamp']}\n{seg['text']}")
    return "\n\n".join(blocks) + "\n"


def convert_srt_to_vtt(srt_content: str) -> str:
    """Convert SRT format to WebVTT format for web HTML5 video players."""
    vtt = "WEBVTT\n\n"
    srt_converted = re.sub(r"(\d\d:\d\d:\d\d),(\d\d\d)", r"\1.\2", srt_content)
    return vtt + srt_converted


class TranslationService:
    """Translation orchestrator using deep-translator and DeepL."""

    def translate_text(self, text: str, target_lang: str = "vi", provider: str = settings.TRANSLATE_PROVIDER) -> str:
        """Translate text with hash caching."""
        text_clean = text.strip()
        if not text_clean:
            return ""

        cache_key = hashlib.md5(f"{provider}:{target_lang}:{text_clean}".encode("utf-8")).hexdigest()
        if cache_key in translation_cache:
            return translation_cache[cache_key]

        translated = ""
        if provider == "deepl" and settings.DEEPL_API_KEY:
            try:
                translator = deepl.Translator(settings.DEEPL_API_KEY)
                res = translator.translate_text(text_clean, target_lang=target_lang.upper())
                translated = res.text
            except Exception as e:
                logger.warning("deepl_failed_fallback_google", error=str(e))
                translated = self._google_translate(text_clean, target_lang)
        else:
            translated = self._google_translate(text_clean, target_lang)

        translation_cache[cache_key] = translated
        return translated

    @staticmethod
    def _google_translate(text: str, target_lang: str) -> str:
        translator = GoogleTranslator(source="auto", target=target_lang)
        return translator.translate(text)

    def translate_srt(self, srt_content: str, target_lang: str = "vi", provider: str = settings.TRANSLATE_PROVIDER) -> Tuple[str, str]:
        """Translate all segments in SRT file while keeping original timestamps."""
        segments = parse_srt(srt_content)
        translated_segments = []

        for seg in segments:
            translated_text = self.translate_text(seg["text"], target_lang=target_lang, provider=provider)
            translated_segments.append({
                "index": seg["index"],
                "timestamp": seg["timestamp"],
                "text": translated_text
            })

        trans_srt = build_srt(translated_segments)
        trans_vtt = convert_srt_to_vtt(trans_srt)
        return trans_srt, trans_vtt


translator_service = TranslationService()
