"""Health check endpoint."""

import time

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])

_start_time = time.time()


@router.get("/health")
async def health_check() -> dict:
    """Return application health status."""
    settings = get_settings()
    return {
        "status": "ok",
        "version": settings.app_version,
        "uptime_seconds": round(time.time() - _start_time, 1),
    }
