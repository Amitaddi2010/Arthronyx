"""
Arthronyx — PubMed Ingestion Client

Fetches orthopedic literature via NCBI E-Utilities with MeSH filtering.
"""

from typing import Any, Dict, List, Optional

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.models.document import DocumentMetadata
from app.models.enums import EvidenceLevel, StudyType, Subdomain

logger = structlog.get_logger(__name__)

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Orthopedic MeSH terms for filtered retrieval
ORTHO_MESH_TERMS = [
    "Orthopedics[MeSH]",
    "Arthroplasty[MeSH]",
    "Fractures, Bone[MeSH]",
    "Spinal Diseases[MeSH]",
    "Joint Diseases[MeSH]",
    "Sports Medicine[MeSH]",
    "Bone Diseases[MeSH]",
    "Musculoskeletal Diseases[MeSH]",
    "Prostheses and Implants[MeSH]",
]


def _build_mesh_query(user_query: str) -> str:
    """Combine user query with orthopedic MeSH filter."""
    mesh_filter = " OR ".join(ORTHO_MESH_TERMS)
    return f"({user_query}) AND ({mesh_filter})"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def search_pubmed(
    query: str,
    max_results: int = 100,
    min_year: Optional[int] = None,
) -> List[str]:
    """Search PubMed and return PMIDs."""
    params: Dict[str, Any] = {
        "db": "pubmed",
        "term": _build_mesh_query(query),
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance",
    }
    if settings.pubmed_api_key:
        params["api_key"] = settings.pubmed_api_key
    if min_year:
        params["mindate"] = f"{min_year}/01/01"
        params["datetype"] = "pdat"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{BASE_URL}/esearch.fcgi", params=params)
        resp.raise_for_status()
        data = resp.json()

    pmids = data.get("esearchresult", {}).get("idlist", [])
    logger.info("pubmed.search_complete", query=query, results=len(pmids))
    return pmids


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def fetch_pubmed_details(pmids: List[str]) -> List[Dict[str, Any]]:
    """Fetch full article details for a list of PMIDs."""
    if not pmids:
        return []

    params: Dict[str, Any] = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
        "rettype": "full",
    }
    if settings.pubmed_api_key:
        params["api_key"] = settings.pubmed_api_key

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(f"{BASE_URL}/esummary.fcgi", params=params)
        resp.raise_for_status()
        data = resp.json()

    articles = []
    result = data.get("result", {})
    for pmid in pmids:
        if pmid in result:
            articles.append(result[pmid])

    logger.info("pubmed.fetched_details", count=len(articles))
    return articles


def _classify_study_type(pub_types: List[str]) -> StudyType:
    """Infer study type from PubMed publication type tags."""
    pub_types_lower = [pt.lower() for pt in pub_types]

    if any("practice guideline" in pt or "guideline" in pt for pt in pub_types_lower):
        return StudyType.GUIDELINE
    if any("meta-analysis" in pt for pt in pub_types_lower):
        return StudyType.META_ANALYSIS
    if any("systematic review" in pt for pt in pub_types_lower):
        return StudyType.SYSTEMATIC_REVIEW
    if any("randomized controlled trial" in pt for pt in pub_types_lower):
        return StudyType.RCT
    if any("clinical trial" in pt for pt in pub_types_lower):
        return StudyType.RCT
    if any("observational" in pt or "cohort" in pt for pt in pub_types_lower):
        return StudyType.COHORT
    if any("case report" in pt for pt in pub_types_lower):
        return StudyType.CASE_REPORT
    return StudyType.NARRATIVE_REVIEW


def _infer_subdomain(title: str, abstract: str = "") -> Subdomain:
    """Infer orthopedic subdomain from title and abstract text."""
    text = (title + " " + abstract).lower()

    subdomain_keywords = {
        Subdomain.ARTHROPLASTY: ["arthroplasty", "joint replacement", "prosthesis", "implant"],
        Subdomain.SPINE: ["spine", "spinal", "vertebr", "disc", "scoliosis", "lumbar", "cervical"],
        Subdomain.TRAUMA: ["fracture", "trauma", "dislocation", "fixation"],
        Subdomain.SPORTS: ["sports", "ligament", "acl", "meniscus", "rotator cuff", "tendon"],
        Subdomain.PEDIATRIC: ["pediatric", "paediatric", "child", "growth plate", "congenital"],
        Subdomain.FOOT_ANKLE: ["foot", "ankle", "hallux", "plantar", "achilles"],
        Subdomain.HAND_UPPER_EXTREMITY: ["hand", "wrist", "elbow", "carpal", "upper extremity"],
    }

    for subdomain, keywords in subdomain_keywords.items():
        if any(kw in text for kw in keywords):
            return subdomain

    return Subdomain.GENERAL


def parse_pubmed_article(article: Dict[str, Any]) -> DocumentMetadata:
    """Parse a PubMed article summary into DocumentMetadata."""
    pub_types = article.get("pubtype", [])
    study_type = _classify_study_type(pub_types)
    title = article.get("title", "")

    # Extract DOI from article IDs
    doi = ""
    article_ids = article.get("articleids", [])
    for aid in article_ids:
        if aid.get("idtype") == "doi":
            doi = aid.get("value", "")
            break
    if not doi:
        doi = f"pmid:{article.get('uid', 'unknown')}"

    # Extract authors
    authors = []
    for author in article.get("authors", []):
        authors.append(author.get("name", ""))

    # Extract year
    pub_date = article.get("pubdate", "")
    year = 2024
    if pub_date:
        try:
            year = int(pub_date[:4])
        except (ValueError, IndexError):
            pass

    from app.models.enums import STUDY_TYPE_EVIDENCE_MAP

    return DocumentMetadata(
        doi=doi,
        title=title,
        authors=authors[:10],  # Limit to first 10 authors
        year=year,
        journal=article.get("fulljournalname", article.get("source", "")),
        study_type=study_type,
        evidence_level=STUDY_TYPE_EVIDENCE_MAP.get(study_type, EvidenceLevel.LEVEL_V),
        sample_size=None,
        subdomain=_infer_subdomain(title),
        country="",
        trial_phase=None,
        abstract="",
        source="PubMed",
    )


# ── Live Search + Fetch (for query pipeline) ─────────────────

async def fetch_pubmed_abstracts(pmids: List[str]) -> List[Dict[str, Any]]:
    """Fetch full article details including abstracts via EFetch XML."""
    if not pmids:
        return []

    params: Dict[str, Any] = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "rettype": "xml",
        "retmode": "xml",
    }
    if settings.pubmed_api_key:
        params["api_key"] = settings.pubmed_api_key
    if settings.pubmed_email:
        params["email"] = settings.pubmed_email

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(f"{BASE_URL}/efetch.fcgi", params=params)
        resp.raise_for_status()

    from xml.etree import ElementTree as ET
    papers = []
    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError as e:
        logger.error("pubmed.xml_parse_error", error=str(e))
        return []

    for article_elem in root.findall(".//PubmedArticle"):
        try:
            medline = article_elem.find("MedlineCitation")
            article = medline.find("Article")

            pmid = medline.findtext("PMID", "")
            title = article.findtext("ArticleTitle", "Untitled")

            # Abstract
            abstract_elem = article.find("Abstract")
            abstract_parts = []
            if abstract_elem is not None:
                for text_elem in abstract_elem.findall("AbstractText"):
                    label = text_elem.get("Label", "")
                    text = text_elem.text or ""
                    if label:
                        abstract_parts.append(f"{label}: {text}")
                    else:
                        abstract_parts.append(text)
            abstract = " ".join(abstract_parts)

            # Journal
            journal = article.findtext(".//Journal/Title", "")

            # Year
            year = 0
            pub_date = article.find(".//PubDate")
            if pub_date is not None:
                year_text = pub_date.findtext("Year", "")
                if year_text and year_text.isdigit():
                    year = int(year_text)
                else:
                    medline_date = pub_date.findtext("MedlineDate", "")
                    if medline_date:
                        for p in medline_date.split():
                            if p.isdigit() and len(p) == 4:
                                year = int(p)
                                break

            # DOI
            doi = ""
            for eid in article.findall(".//ELocationID"):
                if eid.get("EIdType") == "doi":
                    doi = eid.text or ""
                    break
            if not doi:
                article_data = article_elem.find("PubmedData")
                if article_data is not None:
                    for aid in article_data.findall(".//ArticleId"):
                        if aid.get("IdType") == "doi":
                            doi = aid.text or ""
                            break

            # Authors
            authors = []
            author_list = article.find("AuthorList")
            if author_list is not None:
                for author in author_list.findall("Author"):
                    last = author.findtext("LastName", "")
                    first = author.findtext("ForeName", "")
                    if last:
                        authors.append(f"{last} {first}".strip())

            # Publication types & classification
            pub_types = [pt.text for pt in article.findall(".//PublicationTypeList/PublicationType") if pt.text]
            study_type = _classify_study_type(pub_types)
            subdomain = _infer_subdomain(title, abstract)

            evidence_map = {
                StudyType.META_ANALYSIS: "I",
                StudyType.SYSTEMATIC_REVIEW: "I",
                StudyType.RCT: "II",
                StudyType.GUIDELINE: "II",
                StudyType.COHORT: "III",
                StudyType.CASE_REPORT: "IV",
                StudyType.NARRATIVE_REVIEW: "V",
            }

            papers.append({
                "doi": doi or f"PMID:{pmid}",
                "title": title,
                "text": abstract,
                "year": year,
                "journal": journal,
                "authors": authors[:5],
                "study_type": study_type.value if hasattr(study_type, 'value') else str(study_type),
                "evidence_level": evidence_map.get(study_type, "V"),
                "source": "PubMed",
                "subdomain": subdomain.value if hasattr(subdomain, 'value') else str(subdomain),
                "dense_score": 0.0,
            })
        except Exception as e:
            logger.warning("pubmed.article_parse_error", pmid=pmid if 'pmid' in dir() else "?", error=str(e))
            continue

    logger.info("pubmed.abstracts_fetched", count=len(papers))
    return papers


async def search_and_fetch(
    query: str,
    max_results: int = 15,
    year_from: Optional[int] = None,
    study_types: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """High-level: search PubMed + fetch abstracts in one call.

    Returns documents in the same format as the hybrid retrieval pipeline.
    """
    try:
        pmids = await search_pubmed(query, max_results=max_results, min_year=year_from)
        if not pmids:
            return []
        papers = await fetch_pubmed_abstracts(pmids)
        # Filter out papers without abstracts
        papers = [p for p in papers if p.get("text", "").strip()]
        logger.info("pubmed.search_and_fetch_complete", query=query[:60], results=len(papers))
        return papers
    except Exception as e:
        logger.error("pubmed.search_and_fetch_failed", error=str(e))
        return []

