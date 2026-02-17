"""
Arthronyx — ClinicalTrials.gov Stats & Version Route

Provides endpoints for:
  - /ctgov/version   → Data freshness timestamp
  - /ctgov/stats     → Aggregate study statistics for a query
"""

from typing import Any, Dict

import structlog
from fastapi import APIRouter, Query

from app.ingestion.clinicaltrials import get_api_version, get_study_stats

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/ctgov/version")
async def ctgov_version() -> Dict[str, Any]:
    """Check ClinicalTrials.gov API version and data freshness."""
    return await get_api_version()


@router.get("/ctgov/stats")
async def ctgov_stats(
    q: str = Query(..., description="Search query for trial statistics"),
) -> Dict[str, Any]:
    """Get aggregate statistics for matching clinical trials.

    Returns total count, phase distribution, status distribution,
    and study type distribution.
    """
    return await get_study_stats(q)
