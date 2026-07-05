"""Pydantic models for Dubbing endpoint."""
from typing import Optional
from pydantic import BaseModel, Field


class DubRequest(BaseModel):
    job_id: str = Field(..., description="Job ID")
    voice: str = Field(default="female", description="Voice profile ('female', 'male')")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    mix_mode: str = Field(default="overlay", description="Mix mode: 'overlay' or 'replace'")
    original_volume: float = Field(default=0.2, ge=0.0, le=1.0)
    tts_provider: str = Field(default="gtts", description="TTS provider ('gtts' or 'elevenlabs')")


class DubResponse(BaseModel):
    job_id: str
    output_url: str
    error: Optional[str] = None
