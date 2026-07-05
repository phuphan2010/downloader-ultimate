"""Jobs Status and Management API Endpoints."""
from typing import List
from fastapi import APIRouter, HTTPException, status

from app.models.download import JobStatusResponse
from app.services.job_store import get_job, list_jobs
from app.storage.file_manager import file_manager

router = APIRouter()


@router.get("", response_model=List[JobStatusResponse])
async def get_all_jobs():
    """Retrieve status of all submitted jobs."""
    return list_jobs()


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Retrieve status of a specific job by job_id."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_and_delete_job(job_id: str):
    """Cancel and cleanup job data."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )
    file_manager.delete_job(job_id)
    return None
