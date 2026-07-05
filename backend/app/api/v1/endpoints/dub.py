"""Dubbing API Endpoint with Auth."""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_api_key
from app.core.logging import get_logger
from app.models.download import JobStatus
from app.models.dub import DubRequest, DubResponse
from app.services.dubbing import dubbing_service
from app.services.job_store import get_job, update_job
from app.services.translator import parse_srt
from app.services.tts import tts_service
from app.storage.file_manager import file_manager

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=DubResponse)
async def generate_dubbed_video(
    request: DubRequest,
    api_key: str = Depends(get_current_api_key)
):
    """Generate TTS audio and mix it with video audio (requires X-API-Key)."""
    job = get_job(request.job_id)
    if not job or (job.get("api_key") and job.get("api_key") != api_key):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{request.job_id}' not found."
        )

    job_dir = file_manager.get_job_dir(request.job_id)
    downloaded_files = list(job_dir.glob("input_video.*"))
    if not downloaded_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No input video found for this job."
        )

    srt_file = job_dir / "translated_vi.srt"
    if not srt_file.exists():
        srt_file = job_dir / "transcript.srt"

    if not srt_file.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No SRT file found. Please run transcription or translation first."
        )

    video_path = downloaded_files[0]
    tts_audio_path = job_dir / "dubbed_voice.mp3"
    output_video_path = job_dir / "video_dubbed.mp4"

    try:
        update_job(request.job_id, status=JobStatus.DUBBING, progress=60)

        srt_content = srt_file.read_text(encoding="utf-8")
        parsed = parse_srt(srt_content)
        full_text = " ".join([item["text"] for item in parsed if item["text"].strip()]) or "Nội dung video."

        await tts_service.generate_segment_tts(
            full_text, tts_audio_path, lang="vi", provider=request.tts_provider
        )

        await dubbing_service.mix_dubbed_video(
            video_path,
            tts_audio_path,
            output_video_path,
            original_volume=request.original_volume,
            mix_mode=request.mix_mode
        )

        output_url = f"/static/{request.job_id}/video_dubbed.mp4"
        update_job(request.job_id, status=JobStatus.DONE, progress=100, output_url=output_url)

        return DubResponse(job_id=request.job_id, output_url=output_url)
    except Exception as e:
        logger.error("dubbing_failed", job_id=request.job_id, error=str(e))
        update_job(request.job_id, status=JobStatus.FAILED, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dubbing process failed: {str(e)}"
        )
