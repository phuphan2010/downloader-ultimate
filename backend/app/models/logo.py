"""Pydantic models for Logo Overlay endpoint."""
from typing import Optional
from pydantic import BaseModel, Field


class LogoOverlayRequest(BaseModel):
    job_id: str = Field(..., description="Job ID")
    position: str = Field(default="top-right", description="Position: 'top-left', 'top-right', 'bottom-left', 'bottom-right', 'center'")
    size_percent: int = Field(default=15, ge=1, le=50, description="Logo size as % of video width")
    opacity: float = Field(default=0.8, ge=0.0, le=1.0)
    start_time: Optional[float] = Field(default=None, description="Start time in seconds")
    end_time: Optional[float] = Field(default=None, description="End time in seconds")


class LogoOverlayResponse(BaseModel):
    job_id: str
    output_url: str
    error: Optional[str] = None
