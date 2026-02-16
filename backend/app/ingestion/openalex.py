"""
Arthronyx — OpenAlex Metadata Enrichment Client

Uses OpenAlex API to enrich document metadata with citation data,
abstract text, and additional bibliographic details.
"""

from typing import Any, Dict, List, Optional

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = structlog.get_logger(__name__)

BASE_URL = "https://api.openalex.org"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def fetch_work_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Fetch a single work from OpenAlex by DOI."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{BASE_URL}/works/doi:{doi}",
            params={"mailto": settings.pubmed_email},
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def search_works(
    query: str,
    max_results: int = 50,
    filter_concept: str = "orthopedics",
) -> List[Dict[str, Any]]:
    """Search OpenAlex for works matching a query."""
    params = {
        "search": query,
        "filter": f"concepts.display_name.search:{filter_concept}",
        "per_page": min(max_results, 100),
        "mailto": settings.pubmed_email,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{BASE_URL}/works", params=params)
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])
    logger.info("openalex.search_complete", query=query, results=len(results))
    return results


def extract_citation_dois(work: Dict[str, Any]) -> List[str]:
    """Extract DOIs of referenced works from an OpenAlex work."""
    referenced = work.get("referenced_works", [])
    dois = []
    for ref in referenced:
        # OpenAlex IDs are URLs like https://openalex.org/W1234567
        # We need the DOI from the work, not the OpenAlex ID
        if ref.startswith("https://doi.org/"):
            dois.append(ref.replace("https://doi.org/", ""))
    return dois


def extract_abstract(work: Dict[str, Any]) -> str:
    """Reconstruct abstract from OpenAlex inverted abstract index."""
    abstract_index = work.get("abstract_inverted_index")
    if not abstract_index:
        return ""

    # Inverted index: word → [positions]
    words: Dict[int, str] = {}
    for word, positions in abstract_index.items():
        for pos in positions:
            words[pos] = word

    if not words:
        return ""

    max_pos = max(words.keys())
    abstract_parts = [words.get(i, "") for i in range(max_pos + 1)]
    return " ".join(abstract_parts)


async def enrich_metadata(doi: str) -> Optional[Dict[str, Any]]:
    """Enrich a document's metadata using OpenAlex data."""
    work = await fetch_work_by_doi(doi)
    if not work:
        return None

    return {
        "cited_by_count": work.get("cited_by_count", 0),
        "referenced_dois": extract_citation_dois(work),
        "abstract": extract_abstract(work),
        "open_access": work.get("open_access", {}).get("is_oa", False),
        "type": work.get("type", ""),
        "concepts": [
            c.get("display_name", "")
            for c in work.get("concepts", [])[:5]
        ],
    }


# ── Pipeline-Ready Search ─────────────────────────────────────

def _classify_study_type(work_type: str, title: str, abstract: str) -> str:
    """Classify study type from content analysis."""
    combined = f"{title} {abstract}".lower()
    if "meta-analysis" in combined or "meta analysis" in combined:
        return "Meta-Analysis"
    if "systematic review" in combined:
        return "Systematic Review"
    if "randomized" in combined and ("trial" in combined or "controlled" in combined):
        return "RCT"
    if "guideline" in combined:
        return "Guideline"
    if "cohort" in combined:
        return "Cohort"
    if "case-control" in combined or "case control" in combined:
        return "Case-Control"
    if "case series" in combined or "case report" in combined:
        return "Case Series"
    if work_type == "review" or "review" in title.lower():
        return "Review"
    return "Observational"


_EVIDENCE_LEVELS = {
    "Meta-Analysis": "I", "Systematic Review": "I",
    "RCT": "II", "Guideline": "II",
    "Cohort": "III", "Case-Control": "III",
    "Case Series": "IV", "Observational": "IV",
    "Review": "V",
}


async def search_and_fetch(
    query: str,
    max_results: int = 15,
    year_from: Optional[int] = None,
    study_types: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """High-level: search OpenAlex and return pipeline-ready documents.

    Returns documents in the same format as PubMed's search_and_fetch.
    """
    try:
        # Use authenticated request if API key available
        params: Dict[str, Any] = {
            "search": query,
            "per_page": max_results,
            "sort": "relevance_score:desc",
            "select": "id,doi,title,publication_year,type,authorships,primary_location,abstract_inverted_index,cited_by_count,open_access",
        }

        filters = ["type:article|review"]
        if year_from:
            filters.append(f"from_publication_date:{year_from}-01-01")
        params["filter"] = ",".join(filters)

        if settings.openalex_api_key:
            params["api_key"] = settings.openalex_api_key
        params["mailto"] = settings.pubmed_email

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{BASE_URL}/works", params=params)
            resp.raise_for_status()
            data = resp.json()

        works = data.get("results", [])
        papers = []

        for work in works:
            try:
                doi = (work.get("doi") or "").replace("https://doi.org/", "")
                title = work.get("title") or "Untitled"
                abstract = extract_abstract(work)
                if not abstract:
                    continue

                year = work.get("publication_year") or 0

                authors = []
                for a in (work.get("authorships") or [])[:5]:
                    name = (a.get("author") or {}).get("display_name", "")
                    if name:
                        authors.append(name)

                journal = ""
                loc = work.get("primary_location") or {}
                src = loc.get("source") or {}
                journal = src.get("display_name", "")

                work_type = work.get("type", "")
                study_type = _classify_study_type(work_type, title, abstract)

                papers.append({
                    "doi": doi or f"openalex:{work.get('id', '')}",
                    "title": title,
                    "text": abstract,
                    "year": year,
                    "journal": journal,
                    "authors": authors,
                    "study_type": study_type,
                    "evidence_level": _EVIDENCE_LEVELS.get(study_type, "V"),
                    "source": "OpenAlex",
                    "subdomain": "orthopedics",
                    "dense_score": 0.0,
                    "cited_by_count": work.get("cited_by_count", 0),
                })
            except Exception as e:
                logger.warning("openalex.parse_error", error=str(e))
                continue

        logger.info("openalex.search_and_fetch_complete", query=query[:60], results=len(papers))
        return papers

    except Exception as e:
        logger.error("openalex.search_and_fetch_failed", error=str(e))
        return []

