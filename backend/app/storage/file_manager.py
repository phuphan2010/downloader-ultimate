"""File storage and lifecycle management (local storage & auto cleanup)."""
import os
import shutil
import time
from pathlib import Path
from typing import List

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FileManager:
    """Manages job directory creation, file retrieval, and cleanup tasks."""

    def __init__(self, base_path: str = settings.STORAGE_LOCAL_PATH):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def get_job_dir(self, job_id: str) -> Path:
        """Get or create directory for a specific job."""
        job_dir = self.base_path / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir

    def cleanup_old_files(self, ttl_hours: int = settings.FILE_TTL_HOURS) -> int:
        """Delete job directories older than ttl_hours. Returns count of deleted jobs."""
        now = time.time()
        max_age_seconds = ttl_hours * 3600
        deleted_count = 0

        if not self.base_path.exists():
            return 0

        for item in self.base_path.iterdir():
            if item.is_dir():
                try:
                    mtime = item.stat().st_mtime
                    if (now - mtime) > max_age_seconds:
                        shutil.rmtree(item)
                        deleted_count += 1
                        logger.info("job_cleaned_up", job_id=item.name, age_hours=round((now - mtime) / 3600, 1))
                except Exception as e:
                    logger.error("job_cleanup_failed", job_id=item.name, error=str(e))

        return deleted_count

    def delete_job(self, job_id: str) -> bool:
        """Delete job directory manually."""
        job_dir = self.base_path / job_id
        if job_dir.exists():
            shutil.rmtree(job_dir)
            logger.info("job_deleted_manually", job_id=job_id)
            return True
        return False


file_manager = FileManager()
