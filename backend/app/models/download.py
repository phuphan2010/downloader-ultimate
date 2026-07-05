"""Pydantic models for Video Download module."""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field


class VideoQuality(str, Enum):
    BEST = "best"
    HD_720P = "720p"
    SD_480P = "480p"


class PlatformType(str, Enum):
    TIKTOK = "tiktok"
    DOUYIN = "douyin"
    UNKNOWN = "unknown"


class DownloadRequest(BaseModel):
    url: HttpUrl = Field(..., description="TikTok or Douyin video URL")
    quality: VideoQuality = Field(default=VideoQuality.BEST, description="Video quality target")


class JobStatus(str, Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    TRANSLATING = "translating"
    DUBBING = "dubbing"
    BURNING_SUBTITLE = "burning_subtitle"
    ADDING_LOGO = "adding_logo"
    DONE = "done"
    FAILED = "failed"


class DownloadResponse(BaseModel):
    job_id: str
    status: JobStatus = JobStatus.QUEUED
    error: Optional[str] = None


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int = Field(default=0, ge=0, le=100)
    created_at: str
    updated_at: str
    download_url: Optional[str] = None
    output_url: Optional[str] = None
    error: Optional[str] = None
    platform: Optional[PlatformType] = None
