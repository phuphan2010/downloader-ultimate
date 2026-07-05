"""API v1 router — aggregates all endpoint routers."""
from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")

# Routers will be included here as EPICs are completed
# from app.api.v1.endpoints import download, jobs, transcribe, translate
# api_router.include_router(download.router, prefix="/download", tags=["download"])
