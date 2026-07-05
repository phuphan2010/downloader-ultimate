"""API v1 router — aggregates all endpoint routers."""
from fastapi import APIRouter

from app.api.v1.endpoints import download, jobs, transcribe

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(download.router, prefix="/download", tags=["download"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(transcribe.router, prefix="/transcribe", tags=["transcribe"])
