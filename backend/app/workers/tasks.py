"""Celery Worker Task Definitions for asynchronous video processing."""
import asyncio
from typing import Dict, Any, List, Optional
from app.workers.celery_app import celery_app
from app.services.downloader import VideoDownloader
from app.services.pipeline import pipeline_service, PipelineOptions
from app.services.job_store import update_job
from app.models.download import JobStatus
from app.storage.file_manager import file_manager
from app.core.logging import get_logger

logger = get_logger(__name__)


def _run_async(coro):
    """Utility to execute async coroutine inside synchronous Celery worker."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="download_video_task")
def download_video_task(job_id: str, url: str, quality_val: str):
    """Celery task for video download."""
    async def _download():
        update_job(job_id, status=JobStatus.DOWNLOADING, progress=10)
        downloader = VideoDownloader(output_dir=file_manager.base_path)
        file_path = await downloader.download_video(url, job_id)
        update_job(
            job_id,
            status=JobStatus.DONE,
            progress=100,
            download_url=f"/static/{job_id}/{file_path.name}",
            output_url=f"/static/{job_id}/{file_path.name}"
        )

    try:
        _run_async(_download())
    except Exception as e:
        logger.error("celery_download_failed", job_id=job_id, error=str(e))
        update_job(job_id, status=JobStatus.FAILED, error=str(e))


@celery_app.task(name="run_pipeline_task")
def run_pipeline_task(job_id: str, url: str, steps: List[str], options_dict: Dict[str, Any], webhook_url: Optional[str] = None):
    """Celery task for full pipeline execution."""
    async def _pipeline():
        options = PipelineOptions.model_validate(options_dict)
        await pipeline_service.run_pipeline(job_id, url, steps, options, webhook_url)

    try:
        _run_async(_pipeline())
    except Exception as e:
        logger.error("celery_pipeline_failed", job_id=job_id, error=str(e))
        update_job(job_id, status=JobStatus.FAILED, error=str(e))
