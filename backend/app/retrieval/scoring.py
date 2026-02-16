"""
Arthronyx — Time-Weighted Evidence Scoring

Implements the final scoring formula:
    final_score = 0.5 * semantic_relevance + 0.3 * evidence_level_weight + 0.2 * recency_score

Includes evidence hierarchy weighting and publication recency decay.
"""

import math
from datetime import datetime
from typing import Any, Dict

import structlog

from app.config import settings
from app.models.enums import EVIDENCE_LEVEL_WEIGHT

logger = structlog.get_logger(__name__)

# Current year for recency calculations
CURRENT_YEAR = 2026

# Recency decay half-life in years
RECENCY_HALF_LIFE = 5.0


def compute_recency_score(year: int) -> float:
    """Compute recency score using exponential decay.

    Papers from the current year get score ≈1.0.
    Papers from RECENCY_HALF_LIFE years ago get score ≈0.5.
    Score never goes below 0.05.
    """
    if year <= 0:
        return 0.05

    age = max(0, CURRENT_YEAR - year)
    decay = math.exp(-0.693 * age / RECENCY_HALF_LIFE)  # ln(2) ≈ 0.693
    return max(0.05, decay)


def compute_evidence_weight(evidence_level: str) -> float:
    """Map evidence level string to numerical weight.

    Guideline / Meta-analysis (Level I) → 1.0
    RCT (Level II) → 0.8
    Observational (Level III) → 0.6
    Case Series (Level IV) → 0.4
    Case Report / Expert Opinion (Level V) → 0.2
    """
    return EVIDENCE_LEVEL_WEIGHT.get(evidence_level, 0.2)


def compute_final_score(
    semantic_score: float,
    evidence_level: str,
    year: int,
    w_semantic: float | None = None,
    w_evidence: float | None = None,
    w_recency: float | None = None,
) -> Dict[str, float]:
    """Compute the weighted final score.

    final_score = w_semantic * semantic_relevance
                + w_evidence * evidence_level_weight
                + w_recency * recency_score

    Returns dict with all component scores.
    """
    w_s = w_semantic if w_semantic is not None else settings.weight_semantic
    w_e = w_evidence if w_evidence is not None else settings.weight_evidence
    w_r = w_recency if w_recency is not None else settings.weight_recency

    evidence_weight = compute_evidence_weight(evidence_level)
    recency_score = compute_recency_score(year)

    # Normalize semantic score to [0, 1] if needed
    normalized_semantic = max(0.0, min(1.0, semantic_score))

    final = (
        w_s * normalized_semantic
        + w_e * evidence_weight
        + w_r * recency_score
    )

    return {
        "semantic_score": normalized_semantic,
        "evidence_weight": evidence_weight,
        "recency_score": recency_score,
        "final_score": round(final, 6),
    }


def score_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Apply scoring to a retrieved document dict.

    Expects keys: 'dense_score' or 'rerank_score', 'evidence_level', 'year'.
    Adds: 'semantic_score', 'evidence_weight', 'recency_score', 'final_score'.
    """
    # Use rerank_score if available, else dense_score, else bm25_score
    semantic = doc.get("rerank_score", doc.get("dense_score", doc.get("bm25_score", 0.0)))
    evidence_level = doc.get("evidence_level", "V")
    year = doc.get("year", 2000)

    scores = compute_final_score(semantic, evidence_level, year)
    doc.update(scores)
    return doc
