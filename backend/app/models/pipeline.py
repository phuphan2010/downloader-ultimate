"""Pydantic models for Pipeline Orchestrator."""
from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field

from app.models.subtitle import SubtitleStyle


class PipelineDubOptions(BaseModel):
    voice: str = Field(default="female")
    speed: float = Field(default=1.0)
    mix_mode: str = Field(default="overlay")
    original_volume: float = Field(default=0.2)
    tts_provider: str = Field(default="gtts")


class PipelineLogoOptions(BaseModel):
    logo_url: Optional[str] = Field(default=None, description="URL or base64 of logo image")
    position: str = Field(default="top-right")
    size_percent: int = Field(default=15)
    opacity: float = Field(default=0.8)


class PipelineOptions(BaseModel):
    quality: str = Field(default="best")
    subtitle_style: SubtitleStyle = Field(default_factory=SubtitleStyle)
    dub: PipelineDubOptions = Field(default_factory=PipelineDubOptions)
    logo: PipelineLogoOptions = Field(default_factory=PipelineLogoOptions)


class PipelineRequest(BaseModel):
    url: HttpUrl = Field(..., description="TikTok or Douyin video URL")
    steps: List[str] = Field(
        default=["download", "transcribe", "translate", "subtitle", "dub"],
        description="Steps to execute: 'download', 'transcribe', 'translate', 'subtitle', 'dub', 'logo'"
    )
    options: PipelineOptions = Field(default_factory=PipelineOptions)
    webhook_url: Optional[HttpUrl] = Field(default=None, description="HTTPS Webhook URL to call upon completion")


class PipelineResponse(BaseModel):
    job_id: str
    status: str = "queued"
    estimated_time_sec: int = 180
    webhook_registered: bool = False
