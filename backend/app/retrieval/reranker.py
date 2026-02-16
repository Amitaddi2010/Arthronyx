"""
Arthronyx — Cross-Encoder Re-Ranker

PubMedBERT-based cross-encoder for fine-grained relevance scoring.
"""

from typing import Any, Dict, List, Tuple

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

# Lazy-loaded cross-encoder model
_reranker = None


def _get_reranker():
    """Lazy-load the cross-encoder model."""
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder(
            settings.reranker_model,
            max_length=512,
        )
        logger.info("reranker.model_loaded", model=settings.reranker_model)
    return _reranker


def rerank(
    query: str,
    documents: List[Dict[str, Any]],
    top_k: int = 20,
) -> List[Dict[str, Any]]:
    """Re-rank documents using cross-encoder scoring.

    Args:
        query: The search query.
        documents: List of document dicts with 'text' field.
        top_k: Number of top results to return.

    Returns:
        Re-ranked documents with 'rerank_score' added.
    """
    if not documents:
        return []

    model = _get_reranker()

    # Build query-document pairs
    pairs: List[Tuple[str, str]] = [
        (query, doc.get("text", "")[:512])  # Truncate to model max length
        for doc in documents
    ]

    # Score all pairs
    scores = model.predict(pairs, show_progress_bar=False)

    # Attach scores and sort
    for doc, score in zip(documents, scores):
        doc["rerank_score"] = float(score)

    documents.sort(key=lambda x: x["rerank_score"], reverse=True)

    logger.info(
        "reranker.complete",
        input_count=len(documents),
        output_count=min(top_k, len(documents)),
    )

    return documents[:top_k]
