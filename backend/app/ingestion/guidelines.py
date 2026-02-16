"""
Arthronyx — Guideline Ingestion

Handles ingestion of structured medical guidelines from:
- AAOS (American Academy of Orthopaedic Surgeons)
- NICE (National Institute for Health and Care Excellence) MSK guidelines
- Cochrane Reviews
"""

from typing import Any, Dict, List

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.models.document import DocumentMetadata
from app.models.enums import EvidenceLevel, StudyType, Subdomain

logger = structlog.get_logger(__name__)


# ── AAOS Guidelines ──────────────────────────────────────────

AAOS_GUIDELINES_URL = "https://www.aaos.org/quality/quality-programs/clinical-practice-guidelines/"

AAOS_KNOWN_GUIDELINES: List[Dict[str, Any]] = [
    {
        "doi": "aaos:cpg-hip-osteoarthritis-2024",
        "title": "Management of Osteoarthritis of the Hip — AAOS Clinical Practice Guideline",
        "year": 2024,
        "subdomain": Subdomain.ARTHROPLASTY,
    },
    {
        "doi": "aaos:cpg-knee-osteoarthritis-2023",
        "title": "Management of Osteoarthritis of the Knee (Non-Arthroplasty) — AAOS CPG",
        "year": 2023,
        "subdomain": Subdomain.GENERAL,
    },
    {
        "doi": "aaos:cpg-rotator-cuff-2024",
        "title": "Management of Rotator Cuff Injuries — AAOS CPG",
        "year": 2024,
        "subdomain": Subdomain.SPORTS,
    },
    {
        "doi": "aaos:cpg-hip-fractures-2023",
        "title": "Management of Hip Fractures in Older Adults — AAOS CPG",
        "year": 2023,
        "subdomain": Subdomain.TRAUMA,
    },
    {
        "doi": "aaos:cpg-distal-radius-2023",
        "title": "Management of Distal Radius Fractures — AAOS CPG",
        "year": 2023,
        "subdomain": Subdomain.TRAUMA,
    },
]


async def fetch_aaos_guidelines() -> List[DocumentMetadata]:
    """Return known AAOS clinical practice guidelines."""
    guidelines = []
    for entry in AAOS_KNOWN_GUIDELINES:
        guidelines.append(
            DocumentMetadata(
                doi=entry["doi"],
                title=entry["title"],
                authors=["AAOS"],
                year=entry["year"],
                journal="AAOS Clinical Practice Guidelines",
                study_type=StudyType.GUIDELINE,
                evidence_level=EvidenceLevel.LEVEL_I,
                subdomain=entry["subdomain"],
                country="USA",
                source="AAOS",
            )
        )
    logger.info("aaos.guidelines_loaded", count=len(guidelines))
    return guidelines


# ── NICE MSK Guidelines ──────────────────────────────────────

NICE_GUIDELINES: List[Dict[str, Any]] = [
    {
        "doi": "nice:cg177",
        "title": "Osteoarthritis: care and management — NICE CG177",
        "year": 2022,
        "subdomain": Subdomain.GENERAL,
    },
    {
        "doi": "nice:ng59",
        "title": "Low back pain and sciatica in over 16s — NICE NG59",
        "year": 2020,
        "subdomain": Subdomain.SPINE,
    },
    {
        "doi": "nice:ta304",
        "title": "Total hip replacement and resurfacing arthroplasty — NICE TA304",
        "year": 2023,
        "subdomain": Subdomain.ARTHROPLASTY,
    },
    {
        "doi": "nice:ng56",
        "title": "Fractures (non-complex): assessment and management — NICE NG56",
        "year": 2023,
        "subdomain": Subdomain.TRAUMA,
    },
]


async def fetch_nice_guidelines() -> List[DocumentMetadata]:
    """Return known NICE MSK guidelines."""
    guidelines = []
    for entry in NICE_GUIDELINES:
        guidelines.append(
            DocumentMetadata(
                doi=entry["doi"],
                title=entry["title"],
                authors=["NICE"],
                year=entry["year"],
                journal="NICE Guidelines",
                study_type=StudyType.GUIDELINE,
                evidence_level=EvidenceLevel.LEVEL_I,
                subdomain=entry["subdomain"],
                country="UK",
                source="NICE",
            )
        )
    logger.info("nice.guidelines_loaded", count=len(guidelines))
    return guidelines


# ── Cochrane Reviews ─────────────────────────────────────────

COCHRANE_API_URL = "https://www.cochranelibrary.com/api/search"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def search_cochrane(
    query: str,
    max_results: int = 20,
) -> List[DocumentMetadata]:
    """Search Cochrane Library for systematic reviews."""
    # Note: Cochrane API may require authentication in production.
    # This implementation uses their public search endpoint.
    params = {
        "searchBy": "search-manager",
        "searchText": f"{query} AND orthop*",
        "pageSize": max_results,
        "searchType": "standard",
        "resultType": "results",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://www.cochranelibrary.com/cdsr/reviews",
                params=params,
            )
            if resp.status_code != 200:
                logger.warning("cochrane.search_failed", status=resp.status_code)
                return []
    except Exception as e:
        logger.warning("cochrane.search_error", error=str(e))
        return []

    # Placeholder: Cochrane API parsing varies by version
    logger.info("cochrane.search_complete", query=query)
    return []


async def fetch_all_guidelines() -> List[DocumentMetadata]:
    """Aggregate all guideline sources."""
    aaos = await fetch_aaos_guidelines()
    nice = await fetch_nice_guidelines()
    cochrane = await search_cochrane("orthopedic surgery")

    all_guidelines = aaos + nice + cochrane
    logger.info("guidelines.total_loaded", count=len(all_guidelines))
    return all_guidelines
