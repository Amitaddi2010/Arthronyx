"""
Arthronyx — Semantic Scholar Client

Fetches citation graphs and paper details from Semantic Scholar Graph API.
API usage is free (up to limits) or requires an API key for higher throughput.
"""

import asyncio
from typing import Any, Dict, List, Optional

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = structlog.get_logger(__name__)

BASE_URL = "https://api.semanticscholar.org/graph/v1"


class SemanticScholarClient:
    """Client for Semantic Scholar Graph API."""

    def __init__(self, api_key: Optional[str] = None):
        self.headers = {}
        if api_key:
            self.headers["x-api-key"] = api_key

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def get_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Fetch paper details by DOI, PMID, or S2ID.

        paper_id format:
          - "DOI:10.1038/nrn3241"
          - "PMID:123456"
          - "CorpusId:215416146"
          - "649def34f8be52c8b66281af98ae884c09aef38b" (S2ID)
        """
        if paper_id.startswith("10."):
             paper_id = f"DOI:{paper_id}"
        
        url = f"{BASE_URL}/paper/{paper_id}"
        params = {
            "fields": "title,year,abstract,authors,venue,citationCount,referenceCount,openAccessPdf"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url, headers=self.headers, params=params, timeout=10.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.warning("semantic_scholar.paper_not_found", id=paper_id)
                    return None
                logger.error("semantic_scholar.error", status=e.response.status_code, error=str(e))
                raise
            except Exception as e:
                logger.error("semantic_scholar.request_failed", error=str(e))
                raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def get_citations(self, paper_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch papers that cite the given paper."""
        if paper_id.startswith("10."):
             paper_id = f"DOI:{paper_id}"

        url = f"{BASE_URL}/paper/{paper_id}/citations"
        params = {
            "fields": "title,year,venue,contexts,intents,isInfluential",
            "limit": limit
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url, headers=self.headers, params=params, timeout=15.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
            except Exception as e:
                logger.error("semantic_scholar.citations_failed", error=str(e))
                return []

    async def search_papers(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for papers by keyword."""
        url = f"{BASE_URL}/paper/search"
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,year,abstract,authors,venue,externalIds"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url, headers=self.headers, params=params, timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
            except Exception as e:
                logger.error("semantic_scholar.search_failed", error=str(e))
                return []
