"""Pydantic models for Translation endpoint."""
from typing import Optional
from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    job_id: str = Field(..., description="Job ID containing transcript.srt")
    target_lang: str = Field(default="vi", description="Target translation language code")
    provider: str = Field(default="google", description="Translation provider ('google' or 'deepl')")


class TranslateResponse(BaseModel):
    job_id: str
    srt_url: str
    vtt_url: str
    translated_text: str
    target_lang: str
    provider: str
    error: Optional[str] = None
