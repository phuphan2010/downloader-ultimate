"""Pydantic models for Subtitle Burn-in configuration."""
from typing import Optional
from pydantic import BaseModel, Field


class SubtitleStyle(BaseModel):
    font_name: str = Field(default="Arial", description="Font name (e.g. Arial, Roboto)")
    font_size: int = Field(default=24, ge=10, le=72)
    font_color: str = Field(default="#FFFFFF", description="Hex color code")
    outline_color: str = Field(default="#000000", description="Hex outline color code")
    position: str = Field(default="bottom", description="Position: 'top', 'bottom', 'center'")


class SubtitleRequest(BaseModel):
    job_id: str = Field(..., description="Job ID")
    style: SubtitleStyle = Field(default_factory=SubtitleStyle)


class SubtitleResponse(BaseModel):
    job_id: str
    output_url: str
    error: Optional[str] = None
