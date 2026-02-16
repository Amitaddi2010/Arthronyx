"""
Arthronyx — ClinicalTrials.gov Ingestion Client

Fetches orthopedic clinical trial data from the ClinicalTrials.gov API v2.
"""

from typing import Any, Dict, List, Optional

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.models.document import DocumentMetadata
from app.models.enums import EvidenceLevel, StudyType, Subdomain

logger = structlog.get_logger(__name__)

BASE_URL = "https://clinicaltrials.gov/api/v2"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def search_trials(
    query: str,
    max_results: int = 50,
    condition: str = "orthopedic",
) -> List[Dict[str, Any]]:
    """Search ClinicalTrials.gov for relevant trials."""
    params = {
        "query.term": f"{query} AND {condition}",
        "pageSize": min(max_results, 100),
        "format": "json",
        "fields": (
            "NCTId,BriefTitle,OfficialTitle,OverallStatus,Phase,"
            "StudyType,EnrollmentCount,StartDate,CompletionDate,"
            "Condition,InterventionName,LocationCountry,"
            "BriefSummary,DetailedDescription"
        ),
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{BASE_URL}/studies", params=params)
        resp.raise_for_status()
        data = resp.json()

    studies = data.get("studies", [])
    logger.info("clinicaltrials.search_complete", query=query, results=len(studies))
    return studies


def _map_phase(phase_list: List[str]) -> Optional[str]:
    """Map trial phase strings to a standard format."""
    if not phase_list:
        return None
    phases = ", ".join(phase_list)
    return phases


def _infer_subdomain_from_conditions(conditions: List[str]) -> Subdomain:
    """Infer orthopedic subdomain from trial conditions."""
    text = " ".join(conditions).lower()
    from app.ingestion.pubmed import _infer_subdomain
    return _infer_subdomain(text, "")


def parse_trial(study: Dict[str, Any]) -> DocumentMetadata:
    """Parse a ClinicalTrials.gov study to DocumentMetadata."""
    protocol = study.get("protocolSection", {})
    id_module = protocol.get("identificationModule", {})
    status_module = protocol.get("statusModule", {})
    design_module = protocol.get("designModule", {})
    description_module = protocol.get("descriptionModule", {})
    conditions_module = protocol.get("conditionsModule", {})
    contacts_module = protocol.get("contactsLocationsModule", {})

    nct_id = id_module.get("nctId", "")
    title = id_module.get("officialTitle", id_module.get("briefTitle", ""))

    # Year extraction
    start_date = status_module.get("startDateStruct", {}).get("date", "")
    year = 2024
    if start_date:
        try:
            year = int(start_date[:4])
        except (ValueError, IndexError):
            pass

    # Phase → evidence level
    phases = design_module.get("phases", [])
    study_type_str = design_module.get("studyType", "")

    if "INTERVENTIONAL" in study_type_str.upper():
        study_type = StudyType.RCT
        evidence_level = EvidenceLevel.LEVEL_II
    else:
        study_type = StudyType.COHORT
        evidence_level = EvidenceLevel.LEVEL_III

    # Enrollment
    enrollment_info = design_module.get("enrollmentInfo", {})
    sample_size = enrollment_info.get("count")

    # Conditions
    conditions = conditions_module.get("conditions", [])

    # Country
    locations = contacts_module.get("locations", [])
    country = ""
    if locations:
        country = locations[0].get("country", "")

    return DocumentMetadata(
        doi=f"nct:{nct_id}",
        title=title,
        authors=[],
        year=year,
        journal="ClinicalTrials.gov",
        study_type=study_type,
        evidence_level=evidence_level,
        sample_size=sample_size,
        subdomain=_infer_subdomain_from_conditions(conditions),
        country=country,
        trial_phase=_map_phase(phases),
        abstract=description_module.get("briefSummary", ""),
        source="ClinicalTrials.gov",
    )
