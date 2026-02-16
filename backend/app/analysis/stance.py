"""
Arthronyx — Outcome Stance Classifier

Extracts outcome direction from study text:
  - Positive Effect
  - Negative Effect
  - No Significant Difference
  - Mixed
  - Unknown

Uses a hybrid approach:
  1. Keyword/regex heuristics (fast, interpretable)
  2. Optional LLM fallback for ambiguous cases
"""

import re
from typing import Any, Dict, List, Optional

import structlog

from app.models.enums import OutcomeStance

logger = structlog.get_logger(__name__)

# ── Keyword Patterns ─────────────────────────────────────────

POSITIVE_PATTERNS = [
    r"\bsignificant(?:ly)?\s+(?:better|improved|superior|greater|higher|reduced|lower)\b",
    r"\bstatistically\s+significant\s+(?:improvement|benefit|reduction|decrease)\b",
    r"\bp\s*[<≤]\s*0\.0[0-5]\b.*\b(?:improv|better|superior|benefit)\b",
    r"\bfavor(?:s|ed|able|ing)\b",
    r"\bsuperior\s+(?:outcomes?|results?|efficacy)\b",
    r"\b(?:significant|substantial)\s+(?:improvement|benefit)\b",
    r"\brecommend(?:s|ed)?\b.*\b(?:strongly|conditionally)\b",
    r"\beffective\b.*\b(?:reduc|improv|prevent)\b",
]

NEGATIVE_PATTERNS = [
    r"\bsignificant(?:ly)?\s+(?:worse|inferior|higher\s+(?:risk|rate|complication))\b",
    r"\bincreased?\s+(?:risk|complication|mortality|failure)\b",
    r"\bnegative\s+(?:effect|outcome|impact)\b",
    r"\binferior\s+(?:outcomes?|results?)\b",
    r"\bcontraindicated\b",
    r"\bharmful\b",
    r"\bno\s+benefit\b.*\b(?:increased?\s+(?:risk|harm))\b",
]

NO_DIFFERENCE_PATTERNS = [
    r"\bno\s+(?:significant|statistically\s+significant)\s+difference\b",
    r"\bp\s*[>≥]\s*0\.05\b",
    r"\bnon-significant\b",
    r"\bsimilar\s+(?:outcomes?|results?|rates?|efficacy)\b",
    r"\bcomparable\s+(?:outcomes?|results?)\b",
    r"\bequivalent\b",
    r"\bno\s+(?:difference|advantage|superiority)\b",
]

MIXED_PATTERNS = [
    r"\bmixed\s+(?:results?|evidence|findings?)\b",
    r"\bcontradictory\b",
    r"\binconsistent\s+(?:results?|evidence|findings?)\b",
    r"\bhowever.*\bcontrast",
    r"\bon\s+(?:the\s+)?one\s+hand.*\bon\s+(?:the\s+)?other\s+hand\b",
    r"\bsome\s+studies.*\bother\s+studies\b",
]


def classify_stance_heuristic(text: str) -> OutcomeStance:
    """Classify outcome stance using regex pattern matching.

    Applies patterns in priority order and counts matches.
    """
    text_lower = text.lower()

    scores = {
        OutcomeStance.POSITIVE: 0,
        OutcomeStance.NEGATIVE: 0,
        OutcomeStance.NO_SIGNIFICANT_DIFFERENCE: 0,
        OutcomeStance.MIXED: 0,
    }

    for pattern in POSITIVE_PATTERNS:
        if re.search(pattern, text_lower):
            scores[OutcomeStance.POSITIVE] += 1

    for pattern in NEGATIVE_PATTERNS:
        if re.search(pattern, text_lower):
            scores[OutcomeStance.NEGATIVE] += 1

    for pattern in NO_DIFFERENCE_PATTERNS:
        if re.search(pattern, text_lower):
            scores[OutcomeStance.NO_SIGNIFICANT_DIFFERENCE] += 1

    for pattern in MIXED_PATTERNS:
        if re.search(pattern, text_lower):
            scores[OutcomeStance.MIXED] += 1

    # Determine stance: highest count wins, with tiebreaker logic
    max_score = max(scores.values())
    if max_score == 0:
        return OutcomeStance.UNKNOWN

    # If multiple stances have high scores → Mixed
    high_scorers = [stance for stance, s in scores.items() if s == max_score]
    if len(high_scorers) > 1:
        return OutcomeStance.MIXED

    return high_scorers[0]


async def classify_stance_llm(text: str) -> OutcomeStance:
    """Fallback: use LLM to classify outcome stance for ambiguous text."""
    from app.config import settings

    if not settings.llm_api_key:
        return OutcomeStance.UNKNOWN

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.llm_api_key)

        response = await client.chat.completions.create(
            model=settings.llm_model,
            temperature=0,
            max_tokens=50,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a biomedical outcome classifier. "
                        "Classify the following study text into exactly one category: "
                        "POSITIVE, NEGATIVE, NO_SIGNIFICANT_DIFFERENCE, or MIXED. "
                        "Reply with only the category label."
                    ),
                },
                {"role": "user", "content": text[:2000]},
            ],
        )

        label = response.choices[0].message.content.strip().upper()

        mapping = {
            "POSITIVE": OutcomeStance.POSITIVE,
            "NEGATIVE": OutcomeStance.NEGATIVE,
            "NO_SIGNIFICANT_DIFFERENCE": OutcomeStance.NO_SIGNIFICANT_DIFFERENCE,
            "MIXED": OutcomeStance.MIXED,
        }
        return mapping.get(label, OutcomeStance.UNKNOWN)

    except Exception as e:
        logger.warning("stance.llm_fallback_failed", error=str(e))
        return OutcomeStance.UNKNOWN


async def classify_stance(text: str, use_llm_fallback: bool = True) -> OutcomeStance:
    """Classify outcome stance with optional LLM fallback.

    1. Try heuristic classification first.
    2. If result is UNKNOWN and LLM fallback is enabled, use LLM.
    """
    stance = classify_stance_heuristic(text)

    if stance == OutcomeStance.UNKNOWN and use_llm_fallback:
        logger.info("stance.using_llm_fallback")
        stance = await classify_stance_llm(text)

    return stance


async def classify_batch(
    documents: List[Dict[str, Any]],
    use_llm_fallback: bool = False,
) -> List[Dict[str, Any]]:
    """Classify stances for a batch of documents.

    Adds 'outcome_stance' key to each document dict.
    """
    for doc in documents:
        text = doc.get("text", "")
        stance = await classify_stance(text, use_llm_fallback=use_llm_fallback)
        doc["outcome_stance"] = stance.value

    logger.info("stance.batch_classified", count=len(documents))
    return documents
