"""
Arthronyx — Conflict Detection & Evidence Clustering

Groups retrieved studies by outcome direction and explicitly reports conflicts:
  - Number of studies per cluster
  - Aggregate sample sizes
  - Average evidence levels
"""

from collections import defaultdict
from typing import Any, Dict, List

import structlog

from app.models.enums import EVIDENCE_LEVEL_WEIGHT, OutcomeStance
from app.models.query import ClusterStudy, ConflictReport, OutcomeCluster

logger = structlog.get_logger(__name__)


def cluster_by_outcome(documents: List[Dict[str, Any]]) -> List[OutcomeCluster]:
    """Group documents into outcome clusters by stance direction."""
    clusters: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for doc in documents:
        stance = doc.get("outcome_stance", OutcomeStance.UNKNOWN.value)
        clusters[stance].append(doc)

    outcome_clusters = []
    for stance_value, docs in clusters.items():
        # Calculate aggregate stats
        total_sample = sum(doc.get("sample_size", 0) or 0 for doc in docs)

        # Average evidence level
        evidence_weights = [
            EVIDENCE_LEVEL_WEIGHT.get(doc.get("evidence_level", "V"), 0.2)
            for doc in docs
        ]
        avg_weight = sum(evidence_weights) / len(evidence_weights) if evidence_weights else 0.2

        # Map average weight back to approximate level
        avg_level = _weight_to_level(avg_weight)

        # Build study list
        studies = [
            ClusterStudy(
                doi=doc.get("doi", ""),
                title=doc.get("title", ""),
                year=doc.get("year", 0),
                evidence_level=doc.get("evidence_level", "V"),
                sample_size=doc.get("sample_size"),
                journal=doc.get("journal", ""),
            )
            for doc in docs
        ]

        try:
            stance_enum = OutcomeStance(stance_value)
        except ValueError:
            stance_enum = OutcomeStance.UNKNOWN

        outcome_clusters.append(
            OutcomeCluster(
                stance=stance_enum,
                study_count=len(docs),
                total_sample_size=total_sample,
                avg_evidence_level=avg_level,
                studies=studies,
            )
        )

    # Sort: clusters with more studies first
    outcome_clusters.sort(key=lambda c: c.study_count, reverse=True)

    return outcome_clusters


def detect_conflicts(documents: List[Dict[str, Any]]) -> ConflictReport:
    """Detect conflicting evidence across retrieved studies.

    Conflict exists when:
    - Both POSITIVE and NEGATIVE clusters exist
    - OR POSITIVE/NEGATIVE and NO_SIGNIFICANT_DIFFERENCE clusters exist
      with roughly equal study counts
    """
    clusters = cluster_by_outcome(documents)

    stance_counts: Dict[str, int] = {}
    for cluster in clusters:
        stance_counts[cluster.stance.value] = cluster.study_count

    positive_count = stance_counts.get(OutcomeStance.POSITIVE.value, 0)
    negative_count = stance_counts.get(OutcomeStance.NEGATIVE.value, 0)
    no_diff_count = stance_counts.get(OutcomeStance.NO_SIGNIFICANT_DIFFERENCE.value, 0)
    mixed_count = stance_counts.get(OutcomeStance.MIXED.value, 0)

    has_conflict = False
    conflict_summary = ""

    if positive_count > 0 and negative_count > 0:
        has_conflict = True
        conflict_summary = (
            f"Direct conflict detected: {positive_count} study(ies) report positive effects "
            f"while {negative_count} study(ies) report negative effects."
        )
    elif (positive_count > 0 or negative_count > 0) and no_diff_count > 0:
        dominant = "positive" if positive_count > negative_count else "negative"
        dominant_count = max(positive_count, negative_count)
        if dominant_count > 0 and no_diff_count >= dominant_count * 0.5:
            has_conflict = True
            conflict_summary = (
                f"Partial conflict: {dominant_count} study(ies) report {dominant} effects "
                f"while {no_diff_count} study(ies) show no significant difference."
            )
    elif mixed_count > 0:
        has_conflict = True
        conflict_summary = (
            f"{mixed_count} study(ies) report mixed or inconsistent results."
        )

    if not conflict_summary:
        if len(clusters) == 1:
            conflict_summary = f"Consensus: all studies align with '{clusters[0].stance.value}'."
        else:
            conflict_summary = "No major conflict detected among retrieved studies."

    report = ConflictReport(
        has_conflict=has_conflict,
        clusters=clusters,
        conflict_summary=conflict_summary,
    )

    logger.info(
        "conflict.detection_complete",
        has_conflict=has_conflict,
        clusters=len(clusters),
        summary=conflict_summary[:100],
    )

    return report


def _weight_to_level(weight: float) -> str:
    """Map numerical weight back to evidence level string."""
    if weight >= 0.9:
        return "I"
    elif weight >= 0.7:
        return "II"
    elif weight >= 0.5:
        return "III"
    elif weight >= 0.3:
        return "IV"
    else:
        return "V"
