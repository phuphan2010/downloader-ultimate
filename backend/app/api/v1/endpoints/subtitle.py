"""Subtitle Burn-in API Endpoint with Auth."""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_api_key
from app.core.logging import get_logger
from app.models.download import JobStatus
from app.models.subtitle import SubtitleRequest, SubtitleResponse
from app.services.job_store import get_job, update_job
from app.services.subtitle import subtitle_burner_service
from app.storage.file_manager import file_manager

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=SubtitleResponse)
async def burn_subtitle_into_video(
    request: SubtitleRequest,
    api_key: str = Depends(get_current_api_key)
):
    """Hardcode/burn subtitles into the video (requires X-API-Key)."""
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
    output_video_path = job_dir / "video_with_subtitle.mp4"

    try:
        update_job(request.job_id, status=JobStatus.BURNING_SUBTITLE, progress=70)
        await subtitle_burner_service.burn_subtitles(
            video_path, srt_file, output_video_path, style=request.style
        )
        output_url = f"/static/{request.job_id}/video_with_subtitle.mp4"
        update_job(request.job_id, status=JobStatus.DONE, progress=100, output_url=output_url)

        return SubtitleResponse(job_id=request.job_id, output_url=output_url)
    except Exception as e:
        logger.error("subtitle_burn_failed", job_id=request.job_id, error=str(e))
        update_job(request.job_id, status=JobStatus.FAILED, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Subtitle burn failed: {str(e)}"
        )
