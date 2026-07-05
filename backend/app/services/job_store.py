"""Redis-backed job state repository (BUG-05 Fix)."""
from datetime import datetime, timezone
from typing import Dict, Optional, List
from app.models.download import JobStatus, PlatformType
from app.services.redis_store import redis_store


def create_job(job_id: str, platform: PlatformType = PlatformType.UNKNOWN, api_key: Optional[str] = None) -> Dict:
    now = datetime.now(timezone.utc).isoformat()
    job = {
        "job_id": job_id,
        "status": JobStatus.QUEUED.value,
        "progress": 0,
        "created_at": now,
        "updated_at": now,
        "download_url": None,
        "output_url": None,
        "error": None,
        "platform": platform.value,
        "api_key": api_key,
    }
    redis_store.save_job(job_id, job)
    return job


def update_job(job_id: str, **kwargs) -> Optional[Dict]:
    job = redis_store.get_job(job_id)
    if job:
        # Convert Enum instances to strings for JSON serialization
        clean_kwargs = {}
        for k, v in kwargs.items():
            if hasattr(v, "value"):
                clean_kwargs[k] = v.value
            else:
                clean_kwargs[k] = v

        job.update(clean_kwargs)
        job["updated_at"] = datetime.now(timezone.utc).isoformat()
        redis_store.save_job(job_id, job)
        return job
    return None


def get_job(job_id: str) -> Optional[Dict]:
    return redis_store.get_job(job_id)


def list_jobs(api_key: Optional[str] = None) -> List[Dict]:
    return redis_store.list_jobs(api_key=api_key)
