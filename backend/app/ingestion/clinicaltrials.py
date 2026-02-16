"""
Arthronyx — ClinicalTrials.gov v2 API Client

Fetches current clinical trial data to enrich evidence synthesis
with registered interventional/observational studies, their phases,
status, and design characteristics.

API Docs: https://clinicaltrials.gov/data-api/about-api
Endpoint: https://clinicaltrials.gov/api/v2/studies
No API key required.
"""

from typing import Any, Dict, List, Optional

import httpx
import structlog

logger = structlog.get_logger(__name__)

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"


# ── Phase → Evidence Level Mapping ──────────────────────────────

_PHASE_EVIDENCE = {
    "PHASE3": "II",
    "PHASE4": "II",
    "PHASE2": "III",
    "PHASE2_PHASE3": "II",
    "PHASE1_PHASE2": "III",
    "PHASE1": "IV",
    "EARLY_PHASE1": "IV",
    "NA": "IV",
}

_STUDY_TYPE_MAP = {
    "INTERVENTIONAL": "RCT",
    "OBSERVATIONAL": "Observational",
    "EXPANDED_ACCESS": "Observational",
}


def _map_status(status: str) -> str:
    """Convert API status enum to human-readable string."""
    return {
        "RECRUITING": "Recruiting",
        "ACTIVE_NOT_RECRUITING": "Active",
        "COMPLETED": "Completed",
        "ENROLLING_BY_INVITATION": "Enrolling",
        "NOT_YET_RECRUITING": "Not Yet Recruiting",
        "SUSPENDED": "Suspended",
        "TERMINATED": "Terminated",
        "WITHDRAWN": "Withdrawn",
        "UNKNOWN": "Unknown",
    }.get(status, status or "Unknown")


def _extract_description(protocol: dict) -> str:
    """Extract the best available description from a study protocol.

    Prefers the detailed description, falls back to brief summary.
    """
    desc_mod = protocol.get("descriptionModule") or {}
    detailed = (desc_mod.get("detailedDescription") or "").strip()
    brief = (desc_mod.get("briefSummary") or "").strip()
    return detailed or brief


def _extract_conditions(protocol: dict) -> List[str]:
    """Extract condition/disease terms from a study."""
    cond_mod = protocol.get("conditionsModule") or {}
    return (cond_mod.get("conditions") or [])[:8]


def _extract_interventions(protocol: dict) -> List[str]:
    """Extract intervention names from a study."""
    arms_mod = protocol.get("armsInterventionsModule") or {}
    interventions = arms_mod.get("interventions") or []
    return [i.get("name", "") for i in interventions if i.get("name")][:6]


def _extract_authors(protocol: dict) -> List[str]:
    """Extract principal investigators or sponsor name as authors."""
    contacts_mod = protocol.get("contactsLocationsModule") or {}
    investigators = contacts_mod.get("overallOfficials") or []
    names = [inv.get("name", "") for inv in investigators if inv.get("name")]

    if not names:
        sponsor_mod = protocol.get("sponsorCollaboratorsModule") or {}
        lead = sponsor_mod.get("leadSponsor") or {}
        sponsor_name = lead.get("name", "")
        if sponsor_name:
            names = [sponsor_name]

    return names[:5]


def _extract_year(protocol: dict) -> int:
    """Extract publication/start year from dates module."""
    status_mod = protocol.get("statusModule") or {}

    # Try completion date first, then start date
    for date_key in ("completionDateStruct", "startDateStruct"):
        date_obj = status_mod.get(date_key) or {}
        date_str = date_obj.get("date", "")
        if date_str:
            try:
                return int(date_str[:4])
            except (ValueError, IndexError):
                pass

    return 0


async def search_and_fetch(
    query: str,
    max_results: int = 10,
    year_from: Optional[int] = None,
    study_types: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Search ClinicalTrials.gov and return pipeline-ready documents.

    Returns documents in the same format as PubMed/OpenAlex search_and_fetch,
    so they can be merged and deduplicated seamlessly.
    """
    try:
        params: Dict[str, Any] = {
            "query.cond": query,
            "pageSize": min(max_results, 20),
            "countTotal": "true",
            "format": "json",
        }

        # Let the API return relevant fields
        params["fields"] = "|".join([
            "NCTId",
            "BriefTitle",
            "OfficialTitle",
            "BriefSummary",
            "DetailedDescription",
            "OverallStatus",
            "Phase",
            "StudyType",
            "StartDate",
            "CompletionDate",
            "Condition",
            "InterventionName",
            "LeadSponsorName",
            "OverallOfficial",
            "EnrollmentCount",
        ])

        # Apply filters
        filters = []
        if year_from:
            filters.append(f"AREA[StartDate]RANGE[{year_from}-01-01, MAX]")
        # Default: only completed or recruiting studies with results
        filters.append(
            "AREA[OverallStatus]EXPAND[Term]COVER[FullMatch]"
            "RECRUITING,COMPLETED,ACTIVE_NOT_RECRUITING"
        )
        if filters:
            params["filter.advanced"] = " AND ".join(filters)

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        studies = data.get("studies", [])
        papers = []

        for study in studies:
            try:
                protocol = study.get("protocolSection") or {}
                id_mod = protocol.get("identificationModule") or {}
                status_mod = protocol.get("statusModule") or {}
                design_mod = protocol.get("designModule") or {}

                nct_id = id_mod.get("nctId", "")
                title = id_mod.get("officialTitle") or id_mod.get("briefTitle") or "Untitled Trial"
                description = _extract_description(protocol)

                if not description or len(description) < 50:
                    continue  # Skip studies without meaningful description

                # Study type and phase
                study_type_raw = (design_mod.get("studyType") or "INTERVENTIONAL").upper()
                phases = design_mod.get("phases") or []
                phase = phases[0] if phases else "NA"

                study_type = _STUDY_TYPE_MAP.get(study_type_raw, "Observational")
                evidence_level = _PHASE_EVIDENCE.get(phase, "IV")

                # Enrollment
                enrollment_info = design_mod.get("enrollmentInfo") or {}
                enrollment = enrollment_info.get("count", 0)

                # Status
                overall_status = status_mod.get("overallStatus", "")

                year = _extract_year(protocol)
                conditions = _extract_conditions(protocol)
                interventions = _extract_interventions(protocol)
                authors = _extract_authors(protocol)

                papers.append({
                    "doi": f"NCT:{nct_id}",
                    "title": title,
                    "text": description,
                    "year": year,
                    "journal": "ClinicalTrials.gov",
                    "authors": authors,
                    "study_type": f"{study_type} (Phase {phase.replace('PHASE', '').replace('_', '/')})"
                        if phase != "NA" else study_type,
                    "evidence_level": evidence_level,
                    "source": "ClinicalTrials.gov",
                    "subdomain": "orthopedics",
                    "dense_score": 0.0,
                    "nct_id": nct_id,
                    "status": _map_status(overall_status),
                    "enrollment": enrollment,
                    "conditions": conditions,
                    "interventions": interventions,
                })
            except Exception as e:
                logger.warning("clinicaltrials.parse_error", nct_id=nct_id if 'nct_id' in dir() else "?", error=str(e))
                continue

        logger.info(
            "clinicaltrials.search_complete",
            query=query[:60],
            results=len(papers),
            total_found=data.get("totalCount", 0),
        )
        return papers

    except Exception as e:
        logger.error("clinicaltrials.search_failed", error=str(e))
        return []
