"""
Arthronyx — Dense Embedding Retrieval

Semantic search using bge-large-en-v1.5 embeddings via Qdrant.
"""

from typing import Any, Dict, List, Optional

import structlog

from app.config import settings
from app.db.qdrant import search_similar

logger = structlog.get_logger(__name__)

# Lazy-loaded model
_embed_model = None


def _get_model():
    """Lazy-load the sentence-transformer model."""
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        _embed_model = SentenceTransformer(settings.embedding_model)
        logger.info("dense.model_loaded", model=settings.embedding_model)
    return _embed_model


def embed_query(query: str) -> List[float]:
    """Encode a single query string into a dense vector."""
    model = _get_model()
    embedding = model.encode(
        query,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return embedding.tolist()


def dense_search(
    query: str,
    top_k: int = 50,
    subdomain_filter: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    study_types: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Perform dense retrieval via embedding similarity in Qdrant."""
    query_vector = embed_query(query)

    results = search_similar(
        query_embedding=query_vector,
        top_k=top_k,
        subdomain_filter=subdomain_filter,
        year_from=year_from,
        year_to=year_to,
        study_types=study_types,
    )

    # Normalize results to common format
    documents = []
    for hit in results:
        payload = hit.get("payload", {})
        documents.append({
            "doi": payload.get("doi", ""),
            "title": payload.get("title", ""),
            "text": payload.get("text", ""),
            "year": payload.get("year", 0),
            "study_type": payload.get("study_type", ""),
            "evidence_level": payload.get("evidence_level", "V"),
            "subdomain": payload.get("subdomain", ""),
            "journal": payload.get("journal", ""),
            "source": payload.get("source", ""),
            "dense_score": hit.get("score", 0.0),
        })

    logger.info("dense.search_complete", query=query[:50], results=len(documents))
    return documents
