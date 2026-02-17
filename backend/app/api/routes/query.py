"""
Arthronyx — Main Query Endpoint

Orchestrates the full evidence synthesis pipeline:
  1. Receive query + filters
  2. Hybrid retrieval (BM25 + Dense + RRF + Rerank + Time-Weighting)
  3. PubMed + OpenAlex + ClinicalTrials.gov live fallback (parallel fetch)
  4. Stance classification & Conflict detection
  5. LLM synthesis & Citation validation
  6. Audit logging
"""

import asyncio

import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request

from app.ingestion.pipeline import run_full_ingestion
from app.ingestion.pubmed import search_and_fetch as pubmed_search_and_fetch
from app.ingestion.openalex import search_and_fetch as openalex_search_and_fetch
from app.ingestion.clinicaltrials import search_and_fetch as ctgov_search_and_fetch
from app.analysis.extraction import extract_metadata, extract_sample_size
from app.models.query import QueryRequest, QueryResponse
from app.retrieval.hybrid import hybrid_retrieve
from app.retrieval.reranker import rerank
from app.retrieval.scoring import score_document
from app.synthesis.generator import generate_synthesis

router = APIRouter()
logger = structlog.get_logger(__name__)


def _deduplicate_documents(docs):
    """Deduplicate documents by DOI, keeping the first occurrence."""
    seen = set()
    unique = []
    for doc in docs:
        doi = doc.get("doi", "")
        key = doi.lower().strip() if doi else id(doc)
        if key not in seen:
            seen.add(key)
            unique.append(doc)
    return unique


@router.post("/query", response_model=QueryResponse)
async def query_evidence(
    request: QueryRequest,
    req: Request,
) -> QueryResponse:
    """Execute an evidence synthesis query."""
    query_id = getattr(req.state, "request_id", "unknown")
    
    logger.info("api.query_received", query=request.query, id=query_id)

    try:
        # 1. Try local hybrid retrieval first
        documents = await hybrid_retrieve(
            query=request.query,
            top_k=request.max_results,
            subdomain_filter=request.subdomain_filter.value if request.subdomain_filter else None,
            year_from=request.year_from,
            year_to=request.year_to,
            study_types=request.study_types,
        )

        # 2. Fallback: fetch from PubMed + OpenAlex + ClinicalTrials.gov in parallel
        source = "local"
        if not documents:
            logger.info("api.live_search_fallback", query=request.query[:60])

            pubmed_task = pubmed_search_and_fetch(
                query=request.query,
                max_results=request.max_results or 15,
                year_from=request.year_from,
                study_types=request.study_types,
            )
            openalex_task = openalex_search_and_fetch(
                query=request.query,
                max_results=request.max_results or 15,
                year_from=request.year_from,
                study_types=request.study_types,
            )
            ctgov_task = ctgov_search_and_fetch(
                query=request.query,
                max_results=10,
                year_from=request.year_from,
                study_types=request.study_types,
            )

            pubmed_results, openalex_results, ctgov_results = await asyncio.gather(
                pubmed_task, openalex_task, ctgov_task, return_exceptions=True
            )

            # Handle exceptions gracefully
            if isinstance(pubmed_results, Exception):
                logger.warning("api.pubmed_fetch_error", error=str(pubmed_results))
                pubmed_results = []
            if isinstance(openalex_results, Exception):
                logger.warning("api.openalex_fetch_error", error=str(openalex_results))
                openalex_results = []
            if isinstance(ctgov_results, Exception):
                logger.warning("api.ctgov_fetch_error", error=str(ctgov_results))
                ctgov_results = []

            # Combine & deduplicate (PubMed first for priority, then OpenAlex, then ClinicalTrials)
            documents = _deduplicate_documents(
                pubmed_results + openalex_results + ctgov_results
            )
            
            # Apply reranking and scoring to fallback results
            if documents:
                # 0. Extract Metadata (Sample Size, etc.)
                for doc in documents:
                    doc["sample_size"] = extract_sample_size(doc.get("text", ""))
                    # Refine evidence level if needed
                    # logic inside extraction.py can handle this better if integrated fully
                    # For now just sample size is critical

                # 1. Rerank top 50
                documents = rerank(request.query, documents[:50], top_k=25)
                
                # 2. Compute final scores (time-weighted)
                documents = [score_document(doc) for doc in documents]
                documents.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)

            source = "live"

            logger.info(
                "api.live_search_complete",
                pubmed=len(pubmed_results),
                openalex=len(openalex_results),
                ctgov=len(ctgov_results),
                merged=len(documents),
            )

        if not documents:
            logger.warning("api.no_documents_found", query=request.query)
            return QueryResponse(
                success=True,
                query_id=query_id,
                result=None,
                error="No relevant documents found in the corpus, PubMed, OpenAlex, or ClinicalTrials.gov.",
            )

        # 3. Generate Synthesis
        result = await generate_synthesis(request.query, documents)

        # 4. Log Success
        logger.info(
            "api.query_success",
            id=query_id,
            studies_retrieved=len(documents),
            source=source,
            validation_passed=result.validation_passed,
        )

        return QueryResponse(
            success=True,
            query_id=query_id,
            result=result,
        )

    except Exception as e:
        logger.error("api.query_failed", error=str(e), id=query_id)
        return QueryResponse(
            success=False,
            query_id=query_id,
            error=f"Internal processing error: {str(e)}",
        )
