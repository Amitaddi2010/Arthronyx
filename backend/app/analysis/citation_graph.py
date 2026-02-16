"""
Arthronyx — Citation Graph Analysis Module

High-level analysis functions built on the Neo4j citation graph:
  - Co-citation clustering
  - Outdated guideline detection
  - Influence scoring
  - Citation dominance detection
"""

from typing import Any, Dict, List

import structlog

from app.db import neo4j as neo4j_db

logger = structlog.get_logger(__name__)


async def analyze_citation_network(doi: str) -> Dict[str, Any]:
    """Comprehensive citation analysis for a given paper."""
    network = await neo4j_db.get_citation_network(doi, depth=2)
    co_citations = await neo4j_db.get_co_citation_clusters(doi)
    dominance = await neo4j_db.get_citation_dominance(doi)

    return {
        "doi": doi,
        "citation_network": network,
        "co_citations": co_citations,
        "dominance": dominance,
    }


async def get_top_influential_papers(limit: int = 20) -> List[Dict[str, Any]]:
    """Get the most influential papers by citation count."""
    return await neo4j_db.get_influence_scores(limit=limit)


async def find_outdated_guidelines(max_age_years: int = 5) -> List[Dict[str, Any]]:
    """Identify guidelines that may need updating."""
    return await neo4j_db.detect_outdated_guidelines(max_age_years=max_age_years)


async def assess_evidence_currency(
    documents: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Assess whether the retrieved evidence relies on outdated references."""
    outdated = await find_outdated_guidelines()
    outdated_dois = {g["doi"] for g in outdated}

    referenced_outdated = []
    for doc in documents:
        doi = doc.get("doi", "")
        if doi in outdated_dois:
            referenced_outdated.append({
                "doi": doi,
                "title": doc.get("title", ""),
                "year": doc.get("year", 0),
            })

    return {
        "total_outdated_guidelines": len(outdated),
        "referenced_outdated": referenced_outdated,
        "currency_warning": len(referenced_outdated) > 0,
    }
