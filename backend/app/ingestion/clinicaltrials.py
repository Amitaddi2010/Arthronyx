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
API_BASE = "https://clinicaltrials.gov/api/v2"

# ── Shared Headers (WAF bypass) ────────────────────────────────
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://clinicaltrials.gov/",
}


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
    """Extract the best available description from a study protocol."""
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

    for date_key in ("completionDateStruct", "startDateStruct"):
        date_obj = status_mod.get(date_key) or {}
        date_str = date_obj.get("date", "")
        if date_str:
            try:
                return int(date_str[:4])
            except (ValueError, IndexError):
                pass

    return 0


def _extract_primary_outcomes(protocol: dict) -> List[str]:
    """Extract primary outcome measures from study."""
    outcomes_mod = protocol.get("outcomesModule") or {}
    primaries = outcomes_mod.get("primaryOutcomes") or []
    return [o.get("measure", "") for o in primaries if o.get("measure")][:4]


def _extract_countries(protocol: dict) -> List[str]:
    """Extract unique countries from study locations."""
    contacts_mod = protocol.get("contactsLocationsModule") or {}
    locations = contacts_mod.get("locations") or []
    countries = list(dict.fromkeys(
        loc.get("country", "") for loc in locations if loc.get("country")
    ))
    return countries[:5]


# ═══════════════════════════════════════════════════════════════
#  VERSION / FRESHNESS CHECK
# ═══════════════════════════════════════════════════════════════

async def get_api_version() -> Dict[str, Any]:
    """Check ClinicalTrials.gov API version and data freshness.

    Returns:
        Dict with 'apiVersion', 'dataTimestamp', and 'isFresh' flag.
    """
    import asyncio

    def _fetch():
        import requests
        return requests.get(
            f"{API_BASE}/version",
            headers=_HEADERS,
            timeout=10,
        )

    try:
        loop = asyncio.get_running_loop()
        resp = await loop.run_in_executor(None, _fetch)
        resp.raise_for_status()
        data = resp.json()

        logger.info("clinicaltrials.version_check", version=data)
        return {
            "apiVersion": data.get("apiVersion", "unknown"),
            "dataTimestamp": data.get("dataTimestamp", "unknown"),
            "isFresh": True,
        }
    except Exception as e:
        logger.warning("clinicaltrials.version_check_failed", error=str(e))
        return {
            "apiVersion": "unavailable",
            "dataTimestamp": "unavailable",
            "isFresh": False,
        }


# ═══════════════════════════════════════════════════════════════
#  STUDY STATISTICS
# ═══════════════════════════════════════════════════════════════

async def get_study_stats(query: str) -> Dict[str, Any]:
    """Get aggregate statistics for a query from ClinicalTrials.gov.

    Uses the /studies endpoint with countTotal=true to get query-specific
    total count, and derives phase/status/type distributions from results.
    """
    import asyncio

    def _fetch():
        import requests
        return requests.get(
            BASE_URL,
            params={
                "query.term": query,
                "pageSize": 50,  # Fetch up to 50 for distribution analysis
                "countTotal": "true",
                "format": "json",
                "fields": "NCTId,Phase,OverallStatus,StudyType,EnrollmentCount,StartDate",
            },
            headers=_HEADERS,
            timeout=20,
        )

    try:
        loop = asyncio.get_running_loop()
        resp = await loop.run_in_executor(None, _fetch)
        resp.raise_for_status()
        data = resp.json()

        total_count = data.get("totalCount", 0)
        studies = data.get("studies", [])

        # Derive distributions from fetched studies
        phase_dist: Dict[str, int] = {}
        status_dist: Dict[str, int] = {}
        type_dist: Dict[str, int] = {}
        enrollment_total = 0

        for study in studies:
            protocol = study.get("protocolSection") or {}
            design = protocol.get("designModule") or {}
            status_mod = protocol.get("statusModule") or {}

            # Phase
            phases = design.get("phases") or []
            phase = phases[0] if phases else "N/A"
            phase_label = phase.replace("PHASE", "Phase ").replace("_", "/")
            phase_dist[phase_label] = phase_dist.get(phase_label, 0) + 1

            # Status
            status = _map_status(status_mod.get("overallStatus", "Unknown"))
            status_dist[status] = status_dist.get(status, 0) + 1

            # Type
            stype = design.get("studyType", "Unknown")
            type_dist[stype] = type_dist.get(stype, 0) + 1

            # Enrollment
            enroll = (design.get("enrollmentInfo") or {}).get("count", 0)
            if enroll:
                enrollment_total += enroll

        result = {
            "query": query,
            "totalStudies": total_count,
            "sampleSize": len(studies),
            "phaseDistribution": phase_dist,
            "statusDistribution": status_dist,
            "studyTypeDistribution": type_dist,
            "totalEnrollment": enrollment_total,
        }

        logger.info("clinicaltrials.stats_complete", query=query[:60], total=total_count)
        return result

    except Exception as e:
        logger.error("clinicaltrials.stats_failed", error=str(e))
        return {"query": query, "totalStudies": 0, "error": str(e)}


# ═══════════════════════════════════════════════════════════════
#  MAIN SEARCH & FETCH
# ═══════════════════════════════════════════════════════════════

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
            "query.term": query,
            "pageSize": min(max_results, 20),
            "countTotal": "true",
            "format": "json",
        }

        # Expanded field list (includes primary outcomes + locations)
        params["fields"] = ",".join([
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
            "PrimaryOutcomeMeasure",
            "LocationCountry",
        ])

        # Apply filters
        if year_from:
            params["filter.advanced"] = f"AREA[StartDate]RANGE[{year_from}-01-01, MAX]"

        # Filter by status using the supported parameter (EXPAND/COVER not supported)
        params["filter.overallStatus"] = "RECRUITING,COMPLETED,ACTIVE_NOT_RECRUITING"

        def _fetch():
            import requests
            return requests.get(BASE_URL, params=params, headers=_HEADERS, timeout=30)

        import asyncio
        loop = asyncio.get_running_loop()
        resp = await loop.run_in_executor(None, _fetch)
        
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
                primary_outcomes = _extract_primary_outcomes(protocol)
                countries = _extract_countries(protocol)

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
                    "primary_outcomes": primary_outcomes,
                    "countries": countries,
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

