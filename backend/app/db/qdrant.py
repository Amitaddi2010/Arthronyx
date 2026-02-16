"""
Arthronyx — Qdrant Vector Database Layer

Collection management, document upsert, and similarity search.
"""

from typing import Any, Dict, List, Optional

import structlog
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    Range,
    VectorParams,
)

from app.config import settings

logger = structlog.get_logger(__name__)

# ── Client ────────────────────────────────────────────────────

qdrant_client = QdrantClient(
    host=settings.qdrant_host,
    port=settings.qdrant_port,
    timeout=30,
)

VECTOR_DIM = 1024  # bge-large-en-v1.5 dimension


async def init_qdrant() -> None:
    """Create collection if it doesn't exist."""
    collections = qdrant_client.get_collections().collections
    existing_names = [c.name for c in collections]

    if settings.qdrant_collection not in existing_names:
        qdrant_client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(
                size=VECTOR_DIM,
                distance=Distance.COSINE,
            ),
        )
        logger.info("qdrant.collection_created", name=settings.qdrant_collection)
    else:
        logger.info("qdrant.collection_exists", name=settings.qdrant_collection)


# ── Upsert ────────────────────────────────────────────────────

def upsert_chunks(
    chunk_ids: List[str],
    embeddings: List[List[float]],
    payloads: List[Dict[str, Any]],
) -> None:
    """Upsert document chunks with embeddings into Qdrant."""
    points = []
    for idx, (cid, emb, payload) in enumerate(zip(chunk_ids, embeddings, payloads)):
        points.append(
            PointStruct(
                id=idx,
                vector=emb,
                payload={**payload, "chunk_id": cid},
            )
        )

    qdrant_client.upsert(
        collection_name=settings.qdrant_collection,
        points=points,
        wait=True,
    )
    logger.info("qdrant.upserted", count=len(points))


# ── Search ────────────────────────────────────────────────────

def search_similar(
    query_embedding: List[float],
    top_k: int = 50,
    subdomain_filter: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    study_types: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Dense similarity search with optional metadata filters.

    Compatible with both old (.search) and new (.query_points) qdrant-client APIs.
    Returns empty list gracefully if Qdrant is unavailable.
    """
    must_conditions: List[Any] = []

    if subdomain_filter:
        must_conditions.append(
            FieldCondition(key="subdomain", match=MatchValue(value=subdomain_filter))
        )

    if year_from or year_to:
        range_params: Dict[str, Any] = {}
        if year_from:
            range_params["gte"] = year_from
        if year_to:
            range_params["lte"] = year_to
        must_conditions.append(
            FieldCondition(key="year", range=Range(**range_params))
        )

    if study_types:
        for st in study_types:
            must_conditions.append(
                FieldCondition(key="study_type", match=MatchValue(value=st))
            )

    search_filter = Filter(must=must_conditions) if must_conditions else None

    try:
        # Try the newer qdrant-client API first (>= 1.7)
        if hasattr(qdrant_client, 'query_points'):
            from qdrant_client.models import models
            results = qdrant_client.query_points(
                collection_name=settings.qdrant_collection,
                query=query_embedding,
                query_filter=search_filter,
                limit=top_k,
                with_payload=True,
            ).points
        else:
            # Fall back to older API
            results = qdrant_client.search(
                collection_name=settings.qdrant_collection,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=top_k,
                with_payload=True,
            )
    except Exception as e:
        logger.warning("qdrant.search_failed", error=str(e))
        return []

    return [
        {
            "score": hit.score,
            "payload": hit.payload,
        }
        for hit in results
    ]



def get_collection_info() -> Dict[str, Any]:
    """Get collection statistics."""
    info = qdrant_client.get_collection(settings.qdrant_collection)
    return {
        "vectors_count": info.vectors_count,
        "points_count": info.points_count,
        "status": info.status.value,
    }
