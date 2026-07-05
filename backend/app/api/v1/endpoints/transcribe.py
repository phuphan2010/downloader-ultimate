"""Transcription API Endpoint."""
from pathlib import Path
from fastapi import APIRouter, HTTPException, status

from app.core.logging import get_logger
from app.models.download import JobStatus
from app.models.stt import TranscribeRequest, TranscribeResponse
from app.services.audio import audio_service
from app.services.job_store import get_job, update_job
from app.services.stt import stt_service
from app.storage.file_manager import file_manager

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=TranscribeResponse)
async def transcribe_job_audio(request: TranscribeRequest):
    """Extract audio and transcribe video speech to text (generating SRT)."""
    job = get_job(request.job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{request.job_id}' not found."
        )

    job_dir = file_manager.get_job_dir(request.job_id)
    downloaded_files = list(job_dir.glob("input_video.*"))
    if not downloaded_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No input video found for this job. Please perform download first."
        )

    video_path = downloaded_files[0]
    wav_path = job_dir / "audio.wav"
    srt_path = job_dir / "transcript.srt"

    try:
        update_job(request.job_id, status=JobStatus.TRANSCRIBING, progress=30)

        # 1. Extract audio
        await audio_service.extract_audio_wav(video_path, wav_path)

        # 2. Perform STT
        full_text, srt_content, detected_lang = await stt_service.transcribe_audio(
            wav_path, language=request.language
        )

        # 3. Save SRT file
        srt_path.write_text(srt_content, encoding="utf-8")

        srt_url = f"/static/{request.job_id}/transcript.srt"
        update_job(request.job_id, status=JobStatus.DONE, progress=100)

        return TranscribeResponse(
            job_id=request.job_id,
            transcript=full_text,
            srt_url=srt_url,
            detected_language=detected_lang
        )
    except Exception as e:
        logger.error("transcribe_failed", job_id=request.job_id, error=str(e))
        update_job(request.job_id, status=JobStatus.FAILED, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )
