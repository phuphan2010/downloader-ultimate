"""Video Download API Endpoint with Celery Offloading (BUG-06 Fix)."""
import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.core.logging import get_logger
from app.models.download import DownloadRequest, DownloadResponse, JobStatus
from app.services.downloader import validate_and_detect_platform
from app.services.job_store import create_job
from app.workers.tasks import download_video_task

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=DownloadResponse, status_code=status.HTTP_202_ACCEPTED)
async def request_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """Submit a video download request (offloaded to Celery Worker)."""
    url_str = str(request.url)
    is_valid, platform = validate_and_detect_platform(url_str)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL format. Only TikTok and Douyin URLs are supported."
        )

    job_id = str(uuid.uuid4())
    create_job(job_id, platform=platform)

    # Offload to Celery Worker
    try:
        download_video_task.delay(job_id, url_str, request.quality.value)
    except Exception as e:
        logger.warning("celery_dispatch_failed_using_bg_tasks", error=str(e))
        background_tasks.add_task(download_video_task, job_id, url_str, request.quality.value)

    return DownloadResponse(job_id=job_id, status=JobStatus.QUEUED)
