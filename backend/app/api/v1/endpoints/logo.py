"""Logo Overlay API Endpoint with Auth."""
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.deps import get_current_api_key
from app.core.logging import get_logger
from app.models.download import JobStatus
from app.models.logo import LogoOverlayResponse
from app.services.job_store import get_job, update_job
from app.services.logo import logo_service, validate_image_file
from app.storage.file_manager import file_manager

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=LogoOverlayResponse)
async def add_logo_overlay(
    job_id: str = Form(...),
    position: str = Form("top-right"),
    size_percent: int = Form(15),
    opacity: float = Form(0.8),
    start_time: Optional[float] = Form(None),
    end_time: Optional[float] = Form(None),
    logo: UploadFile = File(...),
    api_key: str = Depends(get_current_api_key)
):
    """Upload logo image and burn watermark onto the video (requires X-API-Key)."""
    job = get_job(job_id)
    if not job or (job.get("api_key") and job.get("api_key") != api_key):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found."
        )

    job_dir = file_manager.get_job_dir(job_id)
    downloaded_files = list(job_dir.glob("input_video.*"))
    if not downloaded_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No input video found for this job."
        )

    video_path = downloaded_files[0]
    logo_save_path = job_dir / f"logo_{logo.filename}"

    content = await logo.read()
    logo_save_path.write_bytes(content)

    if not validate_image_file(logo_save_path):
        logo_save_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded logo file is invalid or not a supported image (PNG/JPEG/WEBP)."
        )

    output_video_path = job_dir / "video_with_logo.mp4"

    try:
        update_job(job_id, status=JobStatus.ADDING_LOGO, progress=85)
        await logo_service.overlay_logo(
            video_path,
            logo_save_path,
            output_video_path,
            position=position,
            size_percent=size_percent,
            opacity=opacity,
            start_time=start_time,
            end_time=end_time
        )
        output_url = f"/static/{job_id}/video_with_logo.mp4"
        update_job(job_id, status=JobStatus.DONE, progress=100, output_url=output_url)

        return LogoOverlayResponse(job_id=job_id, output_url=output_url)
    except Exception as e:
        logger.error("logo_overlay_failed", job_id=job_id, error=str(e))
        update_job(job_id, status=JobStatus.FAILED, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logo overlay failed: {str(e)}"
        )
