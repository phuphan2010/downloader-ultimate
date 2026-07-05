"""Pipeline Orchestration service and async webhook notifier."""
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
import httpx

from app.core.logging import get_logger
from app.models.download import JobStatus
from app.models.pipeline import PipelineOptions
from app.services.audio import audio_service
from app.services.downloader import VideoDownloader
from app.services.dubbing import dubbing_service
from app.services.job_store import update_job
from app.services.stt import stt_service
from app.services.subtitle import subtitle_burner_service
from app.services.translator import translator_service, parse_srt
from app.services.tts import tts_service
from app.storage.file_manager import file_manager

logger = get_logger(__name__)


async def trigger_webhook_callback(webhook_url: str, payload: Dict[str, Any], max_retries: int = 3):
    """Send HTTP POST callback to webhook URL with exponential backoff retry."""
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info("sending_webhook_callback", url=webhook_url, attempt=attempt)
                resp = await client.post(webhook_url, json=payload)
                if resp.status_code < 300:
                    logger.info("webhook_callback_success", url=webhook_url, status_code=resp.status_code)
                    return
            except Exception as e:
                logger.warning("webhook_callback_failed", attempt=attempt, error=str(e))
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)


class PipelineService:
    """Batch pipeline runner."""

    @staticmethod
    async def run_pipeline(
        job_id: str,
        url: str,
        steps: List[str],
        options: PipelineOptions,
        webhook_url: Optional[str] = None
    ):
        job_dir = file_manager.get_job_dir(job_id)
        current_video: Optional[Path] = None
        current_srt: Optional[Path] = None

        try:
            # 1. Download
            if "download" in steps:
                update_job(job_id, status=JobStatus.DOWNLOADING, progress=10)
                downloader = VideoDownloader(output_dir=file_manager.base_path)
                current_video = await downloader.download_video(url, job_id)
                update_job(job_id, download_url=f"/static/{job_id}/{current_video.name}")

            # 2. Transcribe (STT)
            if "transcribe" in steps and current_video:
                update_job(job_id, status=JobStatus.TRANSCRIBING, progress=30)
                wav_path = job_dir / "audio.wav"
                srt_path = job_dir / "transcript.srt"
                await audio_service.extract_audio_wav(current_video, wav_path)
                _, srt_content, _ = await stt_service.transcribe_audio(wav_path)
                srt_path.write_text(srt_content, encoding="utf-8")
                current_srt = srt_path

            # 3. Translate
            if "translate" in steps and current_srt:
                update_job(job_id, status=JobStatus.TRANSLATING, progress=50)
                trans_srt, trans_vtt = translator_service.translate_srt(current_srt.read_text(encoding="utf-8"), target_lang="vi")
                out_srt = job_dir / "translated_vi.srt"
                out_vtt = job_dir / "translated_vi.vtt"
                out_srt.write_text(trans_srt, encoding="utf-8")
                out_vtt.write_text(trans_vtt, encoding="utf-8")
                current_srt = out_srt

            # 4. Subtitle Burn
            if "subtitle" in steps and current_video and current_srt:
                update_job(job_id, status=JobStatus.BURNING_SUBTITLE, progress=70)
                sub_video = job_dir / "video_with_subtitle.mp4"
                await subtitle_burner_service.burn_subtitles(current_video, current_srt, sub_video, style=options.subtitle_style)
                current_video = sub_video

            # 5. Dubbing
            if "dub" in steps and current_video and current_srt:
                update_job(job_id, status=JobStatus.DUBBING, progress=85)
                parsed = parse_srt(current_srt.read_text(encoding="utf-8"))
                full_text = " ".join([p["text"] for p in parsed if p["text"].strip()]) or "Nội dung video."
                tts_path = job_dir / "dubbed_voice.mp3"
                dub_video = job_dir / "video_dubbed.mp4"
                await tts_service.generate_segment_tts(full_text, tts_path, lang="vi", provider=options.dub.tts_provider)
                await dubbing_service.mix_dubbed_video(current_video, tts_path, dub_video, original_volume=options.dub.original_volume, mix_mode=options.dub.mix_mode)
                current_video = dub_video

            final_url = f"/static/{job_id}/{current_video.name}" if current_video else None
            update_job(job_id, status=JobStatus.DONE, progress=100, output_url=final_url)

            # Fire webhook if provided
            if webhook_url:
                payload = {
                    "job_id": job_id,
                    "status": "done",
                    "output_url": final_url,
                    "error": None
                }
                await trigger_webhook_callback(webhook_url, payload)

        except Exception as e:
            logger.error("pipeline_execution_error", job_id=job_id, error=str(e))
            update_job(job_id, status=JobStatus.FAILED, error=str(e))
            if webhook_url:
                payload = {
                    "job_id": job_id,
                    "status": "failed",
                    "output_url": None,
                    "error": str(e)
                }
                await trigger_webhook_callback(webhook_url, payload)


pipeline_service = PipelineService()
