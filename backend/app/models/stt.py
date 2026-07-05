"""Pydantic models for Speech-to-Text Transcription."""
from typing import Optional
from pydantic import BaseModel, Field


class TranscribeRequest(BaseModel):
    job_id: str = Field(..., description="Job ID from previous download step")
    language: str = Field(default="auto", description="Source audio language code (e.g. 'zh', 'en', 'auto')")


class TranscribeResponse(BaseModel):
    job_id: str
    transcript: str
    srt_url: str
    detected_language: str
    error: Optional[str] = None
