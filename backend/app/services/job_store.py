"""In-memory job state repository."""
from datetime import datetime, timezone
from typing import Dict, Optional, List
from app.models.download import JobStatus, JobStatusResponse, PlatformType

# Shared in-memory store for API jobs
jobs_db: Dict[str, Dict] = {}


def create_job(job_id: str, platform: PlatformType = PlatformType.UNKNOWN) -> Dict:
    now = datetime.now(timezone.utc).isoformat()
    job = {
        "job_id": job_id,
        "status": JobStatus.QUEUED,
        "progress": 0,
        "created_at": now,
        "updated_at": now,
        "download_url": None,
        "output_url": None,
        "error": None,
        "platform": platform,
    }
    jobs_db[job_id] = job
    return job


def update_job(job_id: str, **kwargs) -> Optional[Dict]:
    if job_id in jobs_db:
        jobs_db[job_id].update(kwargs)
        jobs_db[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        return jobs_db[job_id]
    return None


def get_job(job_id: str) -> Optional[Dict]:
    return jobs_db.get(job_id)


def list_jobs() -> List[Dict]:
    return list(jobs_db.values())
