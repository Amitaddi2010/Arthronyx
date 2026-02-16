"""
Arthronyx — Ingestion Pipeline Orchestrator

Coordinates data fetching, embedding generation, and storage across
PubMed, ClinicalTrials.gov, OpenAlex, and guideline sources.
"""

import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog

from app.config import settings
from app.db.neo4j import add_citation_edge, upsert_paper_node
from app.db.qdrant import upsert_chunks
from app.ingestion.clinical_trials import parse_trial, search_trials
from app.ingestion.guidelines import fetch_all_guidelines
from app.ingestion.openalex import enrich_metadata, extract_citation_dois, fetch_work_by_doi
from app.ingestion.pubmed import fetch_pubmed_details, parse_pubmed_article, search_pubmed
from app.models.document import DocumentChunk, DocumentMetadata

logger = structlog.get_logger(__name__)

# Maximum chunk size in characters
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks."""
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size

        # Try to break at sentence boundary
        if end < len(text):
            last_period = text.rfind(".", start, end)
            if last_period > start + chunk_size // 2:
                end = last_period + 1

        chunks.append(text[start:end].strip())
        start = end - overlap

    return chunks


def generate_chunk_id(doi: str, chunk_index: int) -> str:
    """Generate deterministic chunk ID from DOI and index."""
    raw = f"{doi}::{chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings using sentence-transformers.

    Lazy-loads the model to avoid memory usage when not needed.
    """
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(settings.embedding_model)
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return embeddings.tolist()


async def ingest_document(
    metadata: DocumentMetadata,
    full_text: str = "",
) -> List[DocumentChunk]:
    """Process a single document: chunk → embed → store."""
    # Use abstract if no full text available
    text = full_text if full_text else metadata.abstract
    if not text:
        logger.warning("ingestion.no_text", doi=metadata.doi)
        return []

    # Chunk the text
    text_chunks = chunk_text(text)
    if not text_chunks:
        return []

    # Generate embeddings
    embeddings = await generate_embeddings(text_chunks)

    # Build chunk objects
    chunks = []
    chunk_ids = []
    payloads = []

    for idx, (chunk_text_content, embedding) in enumerate(zip(text_chunks, embeddings)):
        cid = generate_chunk_id(metadata.doi, idx)
        chunk = DocumentChunk(
            chunk_id=cid,
            document_doi=metadata.doi,
            text=chunk_text_content,
            chunk_index=idx,
            embedding=embedding,
        )
        chunks.append(chunk)
        chunk_ids.append(cid)
        payloads.append({
            "doi": metadata.doi,
            "title": metadata.title,
            "year": metadata.year,
            "study_type": metadata.study_type.value,
            "evidence_level": metadata.evidence_level.value,
            "subdomain": metadata.subdomain.value,
            "journal": metadata.journal,
            "source": metadata.source,
            "text": chunk_text_content,
            "chunk_index": idx,
        })

    # Store in Qdrant
    upsert_chunks(chunk_ids, embeddings, payloads)

    # Store in Neo4j
    await upsert_paper_node(
        doi=metadata.doi,
        title=metadata.title,
        year=metadata.year,
        study_type=metadata.study_type.value,
        evidence_level=metadata.evidence_level.value,
        journal=metadata.journal,
    )

    logger.info(
        "ingestion.document_processed",
        doi=metadata.doi,
        chunks=len(chunks),
    )
    return chunks


async def run_full_ingestion(
    query: str = "orthopedic surgery outcomes",
    max_pubmed: int = 100,
    max_trials: int = 50,
) -> Dict[str, Any]:
    """Run the full ingestion pipeline across all sources."""
    started_at = datetime.utcnow()
    stats: Dict[str, Any] = {
        "pubmed": {"found": 0, "ingested": 0},
        "clinical_trials": {"found": 0, "ingested": 0},
        "guidelines": {"found": 0, "ingested": 0},
        "openalex_enriched": 0,
        "citation_edges": 0,
        "errors": [],
    }

    # ── 1. PubMed ─────────────────────────────────────────────
    try:
        pmids = await search_pubmed(query, max_results=max_pubmed)
        articles = await fetch_pubmed_details(pmids)
        stats["pubmed"]["found"] = len(articles)

        for article in articles:
            try:
                metadata = parse_pubmed_article(article)
                await ingest_document(metadata)
                stats["pubmed"]["ingested"] += 1
            except Exception as e:
                stats["errors"].append(f"PubMed article error: {e}")
    except Exception as e:
        stats["errors"].append(f"PubMed search error: {e}")

    # ── 2. ClinicalTrials.gov ─────────────────────────────────
    try:
        trials = await search_trials(query, max_results=max_trials)
        stats["clinical_trials"]["found"] = len(trials)

        for trial in trials:
            try:
                metadata = parse_trial(trial)
                await ingest_document(metadata)
                stats["clinical_trials"]["ingested"] += 1
            except Exception as e:
                stats["errors"].append(f"Trial error: {e}")
    except Exception as e:
        stats["errors"].append(f"ClinicalTrials search error: {e}")

    # ── 3. Guidelines ─────────────────────────────────────────
    try:
        guidelines = await fetch_all_guidelines()
        stats["guidelines"]["found"] = len(guidelines)

        for guideline in guidelines:
            try:
                await ingest_document(guideline)
                stats["guidelines"]["ingested"] += 1
            except Exception as e:
                stats["errors"].append(f"Guideline error: {e}")
    except Exception as e:
        stats["errors"].append(f"Guidelines error: {e}")

    # ── 4. OpenAlex Enrichment + Citation Graph ───────────────
    # Enrich PubMed documents with citation data
    try:
        for article in articles[:50]:  # Limit API calls
            metadata = parse_pubmed_article(article)
            enrichment = await enrich_metadata(metadata.doi)
            if enrichment:
                stats["openalex_enriched"] += 1
                # Add citation edges
                for cited_doi in enrichment.get("referenced_dois", []):
                    try:
                        await add_citation_edge(metadata.doi, cited_doi)
                        stats["citation_edges"] += 1
                    except Exception:
                        pass
    except Exception as e:
        stats["errors"].append(f"OpenAlex enrichment error: {e}")

    elapsed = (datetime.utcnow() - started_at).total_seconds()
    stats["elapsed_seconds"] = elapsed
    logger.info("ingestion.pipeline_complete", **stats)

    return stats
