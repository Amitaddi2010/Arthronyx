"""
Arthronyx — Hybrid Retrieval Orchestrator

Combines BM25 (sparse) + Dense (semantic) retrieval, applies cross-encoder
re-ranking, and computes time-weighted final scores.

Pipeline:
    1. BM25 keyword search → top-50
    2. Dense embedding search → top-50
    3. Reciprocal rank fusion of BM25 + Dense
    4. Cross-encoder re-ranking → top-20
    5. Time-weighted scoring → final top-K
"""

from typing import Any, Dict, List, Optional

import structlog

from app.config import settings
from app.retrieval.bm25 import bm25_index
from app.retrieval.dense import dense_search
from app.retrieval.reranker import rerank
from app.retrieval.scoring import score_document

logger = structlog.get_logger(__name__)

# Reciprocal Rank Fusion constant
RRF_K = 60


def reciprocal_rank_fusion(
    rankings: List[List[Dict[str, Any]]],
    k: int = RRF_K,
) -> List[Dict[str, Any]]:
    """Merge multiple ranked lists using Reciprocal Rank Fusion (RRF).

    RRF score for document d:
        score(d) = Σ 1 / (k + rank_i(d))

    where rank_i(d) is the rank of document d in ranking i.
    """
    scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}

    for ranking in rankings:
        for rank, doc in enumerate(ranking):
            doi = doc.get("doi", "")
            if not doi:
                continue

            rrf_score = 1.0 / (k + rank + 1)
            scores[doi] = scores.get(doi, 0.0) + rrf_score

            # Keep the version with more info
            if doi not in doc_map or len(str(doc)) > len(str(doc_map[doi])):
                doc_map[doi] = doc

    # Sort by RRF score
    sorted_dois = sorted(scores.keys(), key=lambda d: scores[d], reverse=True)

    result = []
    for doi in sorted_dois:
        doc = doc_map[doi].copy()
        doc["rrf_score"] = scores[doi]
        result.append(doc)

    return result


async def hybrid_retrieve(
    query: str,
    top_k: int | None = None,
    subdomain_filter: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    study_types: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Execute the full hybrid retrieval pipeline.

    Returns time-weighted scored documents ready for synthesis.
    """
    final_k = top_k or settings.final_top_k

    logger.info("hybrid.retrieve_start", query=query[:80])

    # ── Step 1: BM25 Keyword Search ──────────────────────────
    bm25_results = bm25_index.search(query, top_k=settings.bm25_top_k)
    logger.info("hybrid.bm25_complete", results=len(bm25_results))

    # ── Step 2: Dense Embedding Search ───────────────────────
    dense_results = dense_search(
        query,
        top_k=settings.dense_top_k,
        subdomain_filter=subdomain_filter,
        year_from=year_from,
        year_to=year_to,
        study_types=study_types,
    )
    logger.info("hybrid.dense_complete", results=len(dense_results))

    # ── Step 3: Reciprocal Rank Fusion ───────────────────────
    fused = reciprocal_rank_fusion([bm25_results, dense_results])
    logger.info("hybrid.rrf_complete", fused=len(fused))

    # ── Step 4: Cross-Encoder Re-Ranking ─────────────────────
    reranked = rerank(query, fused[:settings.rerank_top_k * 2], top_k=settings.rerank_top_k)
    logger.info("hybrid.rerank_complete", results=len(reranked))

    # ── Step 5: Time-Weighted Scoring ────────────────────────
    scored = [score_document(doc) for doc in reranked]
    scored.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)

    final_results = scored[:final_k]
    logger.info(
        "hybrid.retrieve_complete",
        final_count=len(final_results),
        top_score=final_results[0]["final_score"] if final_results else 0.0,
    )

    return final_results
