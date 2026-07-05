"""Video Download API Endpoints."""
import uuid
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.core.config import settings
from app.core.logging import get_logger
from app.models.download import DownloadRequest, DownloadResponse, JobStatus
from app.services.downloader import VideoDownloader, validate_and_detect_platform
from app.services.job_store import create_job, update_job
from app.storage.file_manager import file_manager

logger = get_logger(__name__)
router = APIRouter()


async def process_download_task(job_id: str, url: str, quality_val: str):
    """Background task handling actual yt-dlp download."""
    try:
        update_job(job_id, status=JobStatus.DOWNLOADING, progress=10)
        downloader = VideoDownloader(output_dir=file_manager.base_path)
        file_path: Path = await downloader.download_video(url, job_id)
        update_job(
            job_id,
            status=JobStatus.DONE,
            progress=100,
            download_url=f"/static/{job_id}/{file_path.name}",
            output_url=f"/static/{job_id}/{file_path.name}"
        )
    except Exception as e:
        logger.error("download_background_failed", job_id=job_id, error=str(e))
        update_job(job_id, status=JobStatus.FAILED, error=str(e))


@router.post("", response_model=DownloadResponse, status_code=status.HTTP_202_ACCEPTED)
async def request_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """Submit a video download request (TikTok / Douyin)."""
    url_str = str(request.url)
    is_valid, platform = validate_and_detect_platform(url_str)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL format. Only TikTok and Douyin URLs are supported."
        )

    job_id = str(uuid.uuid4())
    create_job(job_id, platform=platform)
    background_tasks.add_task(process_download_task, job_id, url_str, request.quality.value)

    return DownloadResponse(job_id=job_id, status=JobStatus.QUEUED)
