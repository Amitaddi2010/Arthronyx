"""
Arthronyx — BM25 Keyword Retrieval

Sparse retrieval using BM25 scoring against chunked document corpus.
"""

from typing import Any, Dict, List

import structlog
from rank_bm25 import BM25Okapi

logger = structlog.get_logger(__name__)


class BM25Index:
    """In-memory BM25 index for keyword-based retrieval."""

    def __init__(self) -> None:
        self._corpus: List[Dict[str, Any]] = []
        self._tokenized: List[List[str]] = []
        self._index: BM25Okapi | None = None

    def build(self, documents: List[Dict[str, Any]]) -> None:
        """Build BM25 index from a list of documents.

        Each document must have a 'text' field.
        """
        self._corpus = documents
        self._tokenized = [
            self._tokenize(doc.get("text", "")) for doc in documents
        ]
        if self._tokenized:
            self._index = BM25Okapi(self._tokenized)
        logger.info("bm25.index_built", documents=len(documents))

    def search(self, query: str, top_k: int = 50) -> List[Dict[str, Any]]:
        """Search the BM25 index and return top-k results with scores."""
        if not self._index or not self._corpus:
            logger.warning("bm25.empty_index")
            return []

        tokenized_query = self._tokenize(query)
        scores = self._index.get_scores(tokenized_query)

        # Pair documents with scores and sort
        scored = [
            {**doc, "bm25_score": float(score)}
            for doc, score in zip(self._corpus, scores)
        ]
        scored.sort(key=lambda x: x["bm25_score"], reverse=True)

        return scored[:top_k]

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Basic whitespace + lowercasing tokenizer."""
        import re
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        tokens = text.split()
        # Remove very short tokens
        return [t for t in tokens if len(t) > 2]


# Global singleton
bm25_index = BM25Index()
