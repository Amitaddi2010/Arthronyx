"""
Arthronyx — Citation Validator

Post-generation validation to prevent hallucinated citations.

STRICT RULES:
1. Every DOI in the output must exist in the retrieved documents.
2. If validation fails → flag for regeneration or rejection.
"""

import re
from typing import Any, Dict, List, Set, Tuple

import structlog

logger = structlog.get_logger(__name__)

# Regex patterns for DOI extraction
DOI_PATTERN = re.compile(
    r"""
    (?:doi:\s*|DOI:\s*|https?://doi\.org/)?  # optional prefix
    (10\.\d{4,9}/[^\s,;}\]\)]+)                # capture DOI
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Also match internal identifiers (pmid:, nct:, aaos:, nice:)
INTERNAL_ID_PATTERN = re.compile(
    r"(?:pmid|nct|aaos|nice):[^\s,;}\]\)]+",
    re.IGNORECASE,
)


def extract_cited_dois(text: str) -> Set[str]:
    """Extract all DOI references from generated text."""
    dois = set()

    # Standard DOIs
    for match in DOI_PATTERN.finditer(text):
        doi = match.group(1).rstrip(".,)")
        dois.add(doi)

    # Internal IDs
    for match in INTERNAL_ID_PATTERN.finditer(text):
        dois.add(match.group(0))

    return dois


def validate_citations(
    generated_text: str,
    retrieved_dois: Set[str],
) -> Tuple[bool, List[str], List[str]]:
    """Validate that all citations in generated text exist in retrieved documents.

    Args:
        generated_text: The LLM-generated synthesis text.
        retrieved_dois: Set of DOIs from retrieved documents.

    Returns:
        Tuple of (is_valid, valid_dois, hallucinated_dois).
    """
    cited = extract_cited_dois(generated_text)

    if not cited:
        # No citations found → could be acceptable or a problem
        logger.warning("citation_validator.no_citations_found")
        return True, [], []

    valid = []
    hallucinated = []

    for doi in cited:
        if doi in retrieved_dois or doi.lower() in {d.lower() for d in retrieved_dois}:
            valid.append(doi)
        else:
            hallucinated.append(doi)

    is_valid = len(hallucinated) == 0

    logger.info(
        "citation_validator.result",
        is_valid=is_valid,
        valid_count=len(valid),
        hallucinated_count=len(hallucinated),
        hallucinated=hallucinated[:5],
    )

    return is_valid, valid, hallucinated


def strip_hallucinated_citations(
    text: str,
    hallucinated_dois: List[str],
) -> str:
    """Remove hallucinated DOI references from text.

    Replaces them with [citation removed] markers.
    """
    result = text
    for doi in hallucinated_dois:
        # Escape special regex chars in DOI
        escaped = re.escape(doi)
        result = re.sub(
            rf"\(?\s*(?:doi:\s*)?{escaped}\s*\)?",
            "[citation removed — not in retrieved sources]",
            result,
            flags=re.IGNORECASE,
        )
    return result
