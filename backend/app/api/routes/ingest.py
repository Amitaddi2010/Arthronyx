"""
Arthronyx — Ingestion Endpoint

Trigger manual or scheduled ingestion runs.
"""

from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.ingestion.pipeline import run_full_ingestion

router = APIRouter()


@router.post("/ingest", status_code=202)
async def trigger_ingestion(
    background_tasks: BackgroundTasks,
    query: str = "orthopedic surgery outcomes",
    max_pubmed: int = 100,
    max_trials: int = 50,
) -> Dict[str, Any]:
    """Trigger background ingestion pipeline."""
    background_tasks.add_task(
        run_full_ingestion,
        query=query,
        max_pubmed=max_pubmed,
        max_trials=max_trials,
    )
    return {
        "message": "Ingestion pipeline triggered in background.",
        "params": {
            "query": query,
            "max_pubmed": max_pubmed,
            "max_trials": max_trials,
        },
    }
