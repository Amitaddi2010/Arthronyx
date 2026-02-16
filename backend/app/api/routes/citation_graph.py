"""
Arthronyx — Citation Graph Endpoint

Interactive graph exploration endpoints.
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.analysis.citation_graph import analyze_citation_network

router = APIRouter()


@router.get("/citations/{doi:path}")
async def get_citation_graph(doi: str) -> Dict[str, Any]:
    """Get citation network analysis for a specific credential."""
    try:
        # Decode DOI if needed, but path param usually handles slashes
        return await analyze_citation_network(doi)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
