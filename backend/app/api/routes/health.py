"""
Arthronyx — Health Check Endpoint

Liveness and readiness probes for k8s/docker.
"""

from typing import Any, Dict

from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Service health check."""
    return {
        "status": "healthy",
        "version": "1.0.0",
    }
