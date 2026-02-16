"""
Arthronyx — Neo4j Citation Graph Layer

Citation relationship management, co-citation analysis, and influence scoring.
"""

from typing import Any, Dict, List, Optional

import structlog
from neo4j import AsyncGraphDatabase

from app.config import settings

logger = structlog.get_logger(__name__)

# ── Driver ────────────────────────────────────────────────────

neo4j_driver = AsyncGraphDatabase.driver(
    settings.neo4j_uri,
    auth=(settings.neo4j_user, settings.neo4j_password),
    max_connection_pool_size=50,
)


async def verify_connectivity() -> None:
    """Verify Neo4j connection on startup."""
    async with neo4j_driver.session() as session:
        await session.run("RETURN 1")
    logger.info("neo4j.connected", uri=settings.neo4j_uri)


# ── Schema Setup ─────────────────────────────────────────────

async def init_neo4j_schema() -> None:
    """Create constraints and indexes."""
    async with neo4j_driver.session() as session:
        await session.run(
            "CREATE CONSTRAINT paper_doi IF NOT EXISTS "
            "FOR (p:Paper) REQUIRE p.doi IS UNIQUE"
        )
        await session.run(
            "CREATE INDEX paper_year IF NOT EXISTS FOR (p:Paper) ON (p.year)"
        )
    logger.info("neo4j.schema_initialized")


# ── Node Operations ──────────────────────────────────────────

async def upsert_paper_node(
    doi: str,
    title: str,
    year: int,
    study_type: str,
    evidence_level: str,
    journal: str = "",
) -> None:
    """Create or update a paper node."""
    query = """
    MERGE (p:Paper {doi: $doi})
    SET p.title = $title,
        p.year = $year,
        p.study_type = $study_type,
        p.evidence_level = $evidence_level,
        p.journal = $journal,
        p.updated_at = datetime()
    """
    async with neo4j_driver.session() as session:
        await session.run(
            query,
            doi=doi,
            title=title,
            year=year,
            study_type=study_type,
            evidence_level=evidence_level,
            journal=journal,
        )


async def add_citation_edge(citing_doi: str, cited_doi: str) -> None:
    """Create a CITES relationship between two papers."""
    query = """
    MATCH (a:Paper {doi: $citing_doi})
    MATCH (b:Paper {doi: $cited_doi})
    MERGE (a)-[:CITES]->(b)
    """
    async with neo4j_driver.session() as session:
        await session.run(query, citing_doi=citing_doi, cited_doi=cited_doi)


# ── Citation Analysis ────────────────────────────────────────

async def get_citation_network(doi: str, depth: int = 2) -> Dict[str, Any]:
    """Get the citation network around a paper up to N hops."""
    query = """
    MATCH path = (p:Paper {doi: $doi})-[:CITES*1..""" + str(depth) + """]->(cited:Paper)
    RETURN p.doi AS source,
           [n IN nodes(path) | {doi: n.doi, title: n.title, year: n.year}] AS chain,
           length(path) AS depth
    LIMIT 200
    """
    async with neo4j_driver.session() as session:
        result = await session.run(query, doi=doi)
        records = [record.data() async for record in result]
    return {"doi": doi, "network": records}


async def get_co_citation_clusters(doi: str) -> List[Dict[str, Any]]:
    """Find papers frequently co-cited with the given paper."""
    query = """
    MATCH (a:Paper)-[:CITES]->(target:Paper {doi: $doi}),
          (a)-[:CITES]->(co_cited:Paper)
    WHERE co_cited.doi <> $doi
    WITH co_cited, count(a) AS co_citation_count
    ORDER BY co_citation_count DESC
    LIMIT 20
    RETURN co_cited.doi AS doi,
           co_cited.title AS title,
           co_cited.year AS year,
           co_citation_count
    """
    async with neo4j_driver.session() as session:
        result = await session.run(query, doi=doi)
        return [record.data() async for record in result]


async def get_influence_scores(limit: int = 20) -> List[Dict[str, Any]]:
    """Compute influence scores based on incoming citation count."""
    query = """
    MATCH (cited:Paper)<-[:CITES]-(citing:Paper)
    WITH cited, count(citing) AS citation_count
    ORDER BY citation_count DESC
    LIMIT $limit
    RETURN cited.doi AS doi,
           cited.title AS title,
           cited.year AS year,
           cited.evidence_level AS evidence_level,
           citation_count AS influence_score
    """
    async with neo4j_driver.session() as session:
        result = await session.run(query, limit=limit)
        return [record.data() async for record in result]


async def detect_outdated_guidelines(max_age_years: int = 5) -> List[Dict[str, Any]]:
    """Find guidelines that are heavily cited but older than threshold."""
    current_year = 2026
    cutoff = current_year - max_age_years
    query = """
    MATCH (cited:Paper)<-[:CITES]-(citing:Paper)
    WHERE cited.study_type = 'Guideline' AND cited.year < $cutoff
    WITH cited, count(citing) AS citation_count
    ORDER BY citation_count DESC
    LIMIT 20
    RETURN cited.doi AS doi,
           cited.title AS title,
           cited.year AS year,
           citation_count,
           $current_year - cited.year AS age_years
    """
    async with neo4j_driver.session() as session:
        result = await session.run(
            query, cutoff=cutoff, current_year=current_year
        )
        return [record.data() async for record in result]


async def get_citation_dominance(doi: str) -> Optional[Dict[str, Any]]:
    """Check if a single paper dominates the citation landscape for a topic."""
    query = """
    MATCH (p:Paper {doi: $doi})<-[:CITES]-(citing:Paper)
    WITH count(citing) AS in_citations
    MATCH (any:Paper)<-[:CITES]-(c:Paper)
    WITH in_citations, count(c) AS total_citations
    RETURN in_citations,
           total_citations,
           CASE WHEN total_citations > 0
                THEN round(toFloat(in_citations) / total_citations * 100, 2)
                ELSE 0 END AS dominance_pct
    """
    async with neo4j_driver.session() as session:
        result = await session.run(query, doi=doi)
        record = await result.single()
        return record.data() if record else None
