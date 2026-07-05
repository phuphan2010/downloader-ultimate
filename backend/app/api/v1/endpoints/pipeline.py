"""Pipeline API Endpoint with Celery Worker Offloading (BUG-06 Fix)."""
import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.core.logging import get_logger
from app.models.pipeline import PipelineRequest, PipelineResponse
from app.services.downloader import validate_and_detect_platform
from app.services.job_store import create_job
from app.workers.tasks import run_pipeline_task

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=PipelineResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_pipeline_job(request: PipelineRequest, background_tasks: BackgroundTasks):
    """Submit a full end-to-end video processing pipeline job offloaded to Celery Worker."""
    url_str = str(request.url)
    is_valid, platform = validate_and_detect_platform(url_str)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL. Only TikTok and Douyin URLs are accepted."
        )

    job_id = str(uuid.uuid4())
    create_job(job_id, platform=platform)

    webhook_url_str = str(request.webhook_url) if request.webhook_url else None
    options_dict = request.options.model_dump()

    # Offload task to Celery Worker Queue
    try:
        run_pipeline_task.delay(job_id, url_str, request.steps, options_dict, webhook_url_str)
    except Exception as e:
        logger.warning("celery_dispatch_failed_using_bg_tasks", error=str(e))
        background_tasks.add_task(run_pipeline_task, job_id, url_str, request.steps, options_dict, webhook_url_str)

    return PipelineResponse(
        job_id=job_id,
        status="queued",
        estimated_time_sec=180,
        webhook_registered=webhook_url_str is not None
    )
