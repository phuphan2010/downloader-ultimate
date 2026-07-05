"""Jobs Status and Management API Endpoints (BUG-07 Privacy Fix)."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_api_key
from app.models.download import JobStatusResponse
from app.services.job_store import get_job, list_jobs
from app.storage.file_manager import file_manager

router = APIRouter()


@router.get("", response_model=List[JobStatusResponse])
async def get_all_jobs(api_key: str = Depends(get_current_api_key)):
    """Retrieve status of submitted jobs for the caller's API Key (Privacy Isolated)."""
    return list_jobs(api_key=api_key)


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, api_key: str = Depends(get_current_api_key)):
    """Retrieve status of a specific job by job_id (Privacy Protected)."""
    job = get_job(job_id)
    if not job or (job.get("api_key") and job.get("api_key") != api_key):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_and_delete_job(job_id: str, api_key: str = Depends(get_current_api_key)):
    """Cancel and cleanup job data (Privacy Protected)."""
    job = get_job(job_id)
    if not job or (job.get("api_key") and job.get("api_key") != api_key):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )
    file_manager.delete_job(job_id)
    return None
