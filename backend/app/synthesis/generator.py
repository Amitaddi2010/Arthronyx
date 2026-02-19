"""
Arthronyx — Structured Evidence Synthesis Generator

LLM-powered synthesis that STRICTLY:
  1. Uses only information from retrieved chunks
  2. Cites DOIs for every factual statement
  3. Outputs the mandatory 8-section format
  4. Temperature = 0
  5. Validates citations post-generation
"""

from collections import Counter
from typing import Any, Dict, List

import structlog

from app.analysis.conflict import detect_conflicts
from app.analysis.stance import classify_batch
from app.config import settings
from app.models.enums import OutcomeStance
from app.models.query import (
    Citation,
    ConflictReport,
    EvidenceOverview,
    StudyTypeDistribution,
    SynthesisResult,
)
from app.synthesis.citation_validator import (
    extract_cited_dois,
    strip_hallucinated_citations,
    validate_citations,
)
from app.synthesis.disclaimer import get_disclaimer

logger = structlog.get_logger(__name__)

MAX_REGENERATION_ATTEMPTS = 2


def _build_evidence_overview(documents: List[Dict[str, Any]]) -> EvidenceOverview:
    """Build evidence overview statistics from retrieved documents."""
    type_counts = Counter(doc.get("study_type", "Unknown") for doc in documents)
    years = [doc.get("year", 0) for doc in documents if doc.get("year", 0) > 0]
    subdomains = list(set(doc.get("subdomain", "") for doc in documents if doc.get("subdomain")))

    year_range = f"{min(years)}–{max(years)}" if years else "N/A"

    return EvidenceOverview(
        total_studies=len(documents),
        type_distribution=[
            StudyTypeDistribution(study_type=st, count=c)
            for st, c in type_counts.most_common()
        ],
        year_range=year_range,
        subdomains_covered=subdomains,
    )


def _build_citations(documents: List[Dict[str, Any]]) -> List[Citation]:
    """Build citation list from retrieved documents."""
    citations = []
    seen_dois = set()

    for doc in documents:
        doi = doc.get("doi", "")
        if doi and doi not in seen_dois:
            seen_dois.add(doi)
            authors = doc.get("authors", [])
            if isinstance(authors, list) and authors:
                authors_short = f"{authors[0]} et al." if len(authors) > 1 else authors[0]
            else:
                authors_short = "Unknown"

            citations.append(
                Citation(
                    doi=doi,
                    title=doc.get("title", ""),
                    authors_short=authors_short,
                    year=doc.get("year", 0),
                    journal=doc.get("journal", ""),
                )
            )

    return citations


def _build_context_block(documents: List[Dict[str, Any]]) -> str:
    """Build the evidence context string for the LLM prompt."""
    blocks = []
    for i, doc in enumerate(documents, 1):
        block = (
            f"[{i}] DOI: {doc.get('doi', 'N/A')}\n"
            f"    Title: {doc.get('title', 'N/A')}\n"
            f"    Year: {doc.get('year', 'N/A')} | "
            f"Type: {doc.get('study_type', 'N/A')} | "
            f"Level: {doc.get('evidence_level', 'N/A')}\n"
            f"    Outcome: {doc.get('outcome_stance', 'Unknown')}\n"
            f"    Text: {doc.get('text', '')[:800]}\n"
        )
        blocks.append(block)

    return "\n".join(blocks)


SYNTHESIS_SYSTEM_PROMPT = """You are Arthronyx, an evidence synthesis engine for orthopedic medicine.

STRICT RULES:
1. You MUST ONLY use information from the provided evidence blocks below.
2. Every factual statement MUST include a DOI citation in format (DOI: ...).
3. If evidence is missing for a claim, write: "No evidence found in retrieved sources."
4. Do NOT generate any information beyond what is in the provided evidence.
5. Do NOT provide personalized treatment recommendations.
6. Do NOT provide patient-specific advice.

OUTPUT FORMAT (mandatory):
1. Evidence Synthesis — Narrative synthesis of the evidence
2. Limitations — Bullet list of limitations in the evidence base
3. Final Evidence Position — A single paragraph summarizing the overall evidence position

Cite every claim with the DOI from the evidence blocks."""


async def generate_synthesis(
    query: str,
    documents: List[Dict[str, Any]],
) -> SynthesisResult:
    """Generate structured evidence synthesis from retrieved documents.

    Full pipeline:
    1. Classify stances for all documents
    2. Detect conflicts
    3. Build evidence overview
    4. Generate LLM synthesis (temperature=0)
    5. Validate citations
    6. Assemble final 8-section output
    """
    # ── Step 1: Stance Classification ────────────────────────
    documents = await classify_batch(documents, use_llm_fallback=False)

    # ── Step 2: Conflict Detection ───────────────────────────
    conflict_report = detect_conflicts(documents)

    # ── Step 3: Evidence Overview ────────────────────────────
    evidence_overview = _build_evidence_overview(documents)

    # ── Step 4: Build Priority Evidence ──────────────────────
    priority_evidence = []
    for doc in documents[:5]:  # Top 5 by final_score
        priority_evidence.append({
            "doi": doc.get("doi", ""),
            "title": doc.get("title", ""),
            "year": str(doc.get("year", "")),
            "study_type": doc.get("study_type", ""),
            "evidence_level": doc.get("evidence_level", ""),
            "final_score": str(round(doc.get("final_score", 0), 4)),
            "outcome": doc.get("outcome_stance", "Unknown"),
        })

    # ── Step 5: LLM Synthesis Generation ─────────────────────
    context = _build_context_block(documents)
    retrieved_dois = {doc.get("doi", "") for doc in documents}

    synthesis_text = ""
    limitations: List[str] = []
    final_position = ""
    validation_passed = False

    for attempt in range(MAX_REGENERATION_ATTEMPTS + 1):
        synthesis_text, limitations, final_position = await _call_llm(
            query, context, conflict_report, documents
        )

        # ── Step 6: Citation Validation ──────────────────────
        # Skip validation if we are in fallback mode (identified by the specific header)
        if "**Note: detailed synthesis requires an LLM API key" in synthesis_text or "Detailed AI synthesis is unavailable" in synthesis_text:
            validation_passed = True
            break

        is_valid, valid_dois, hallucinated_dois = validate_citations(
            synthesis_text + " " + final_position,
            retrieved_dois,
        )

        if is_valid:
            validation_passed = True
            break
        elif attempt < MAX_REGENERATION_ATTEMPTS:
            logger.warning(
                "synthesis.citation_validation_failed",
                attempt=attempt + 1,
                hallucinated=hallucinated_dois,
            )
            # Strip hallucinated citations and retry
            synthesis_text = strip_hallucinated_citations(synthesis_text, hallucinated_dois)
            final_position = strip_hallucinated_citations(final_position, hallucinated_dois)
        else:
            logger.error("synthesis.max_regeneration_attempts_exceeded")
            synthesis_text = strip_hallucinated_citations(synthesis_text, hallucinated_dois)
            final_position = strip_hallucinated_citations(final_position, hallucinated_dois)
            validation_passed = False

    # ── Step 7: Assemble Result ──────────────────────────────
    return SynthesisResult(
        clinical_question=query,
        evidence_overview=evidence_overview,
        priority_evidence=priority_evidence,
        conflict_report=conflict_report,
        evidence_synthesis=synthesis_text,
        limitations=limitations,
        final_position=final_position,
        disclaimer=get_disclaimer(),
        citations=_build_citations(documents),
        validation_passed=validation_passed,
    )


async def _call_llm(
    query: str,
    context: str,
    conflict_report: ConflictReport,
    documents: List[Dict[str, Any]],
) -> tuple[str, List[str], str]:
    """Call the LLM to generate synthesis text.

    Returns (synthesis_text, limitations, final_position).
    """
    if not settings.llm_api_key:
        # Fallback: generate without LLM
        return _generate_fallback(query, documents, conflict_report)

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )

        conflict_context = ""
        if conflict_report.has_conflict:
            conflict_context = (
                f"\n\nCONFLICT ALERT: {conflict_report.conflict_summary}\n"
                f"Clusters: {len(conflict_report.clusters)} outcome groups detected.\n"
            )

        user_prompt = (
            f"Clinical Question: {query}\n\n"
            f"Retrieved Evidence ({context.count('[') - 1} studies):\n{context}"
            f"{conflict_context}\n\n"
            f"Generate the evidence synthesis following the mandatory format. "
            f"Cite every claim with a DOI."
        )

        response = await client.chat.completions.create(
            model=settings.llm_model,
            temperature=0,
            max_tokens=3000,
            messages=[
                {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )

        raw = response.choices[0].message.content or ""
        return _parse_llm_output(raw)

    except Exception as e:
        logger.error("synthesis.llm_error", error=str(e), error_type=type(e).__name__)
        import traceback
        logger.error("synthesis.llm_traceback", traceback=traceback.format_exc())
        return _generate_fallback(query, documents, conflict_report)


def _parse_llm_output(raw: str) -> tuple[str, List[str], str]:
    """Parse LLM output into sections."""
    synthesis = ""
    limitations: List[str] = []
    final_position = ""

    sections = raw.split("\n\n")

    current_section = "synthesis"
    for section in sections:
        lower = section.strip().lower()
        if "limitation" in lower[:30]:
            current_section = "limitations"
            continue
        elif "final evidence position" in lower[:40] or "final position" in lower[:30]:
            current_section = "final_position"
            continue

        if current_section == "synthesis":
            synthesis += section + "\n\n"
        elif current_section == "limitations":
            for line in section.split("\n"):
                line = line.strip().lstrip("•-*● ")
                if line:
                    limitations.append(line)
        elif current_section == "final_position":
            final_position += section + " "

    return synthesis.strip(), limitations, final_position.strip()


def _generate_fallback(
    query: str,
    documents: List[Dict[str, Any]],
    conflict_report: ConflictReport,
) -> tuple[str, List[str], str]:
    """Generate a structure summary without LLM access."""
    
    # 1. Build a structured summary of the top evidence
    synthesis_parts = [
        "> **Note:** Detailed AI synthesis is unavailable at the moment. Below is a structured summary of the retrieved evidence based on metadata.\n"
    ]
    
    # Group by outcome stance
    by_stance = {}
    for doc in documents:
        stance = doc.get("outcome_stance", "Unknown")
        if stance not in by_stance:
            by_stance[stance] = []
        by_stance[stance].append(doc)
        
    for stance, docs in by_stance.items():
        if not docs:
            continue
        synthesis_parts.append(f"### {stance} ({len(docs)} studies)")
        for doc in docs[:5]: # Top 5 per stance
            title = doc.get("title", "Untitled")
            year = doc.get("year", "N/A")
            doi = doc.get("doi", "")
            level = doc.get("evidence_level", "V")
            
            # Format: - **Title** (Year) [Level]
            #          *DOI: ...*
            synthesis_parts.append(
                f"- **{title}** ({year}) [Level {level}]\n"
                f"  *DOI: {doi}*"
            )
        if len(docs) > 5:
            synthesis_parts.append(f"- *...and {len(docs) - 5} more retrieval(s)*")
        synthesis_parts.append("")

    synthesis = "\n".join(synthesis_parts)

    limitations = [
        "Synthesis generated in fallback mode (no LLM inference).",
        "Groupings are based on heuristic keyword classification, not semantic understanding.",
        "Manual verification of study details is recommended.",
    ]

    conflict_note = ""
    if conflict_report.has_conflict:
        conflict_note = f" {conflict_report.conflict_summary}"

    final_position = (
        f"Automated analysis identified {len(documents)} relevant studies for '{query}'. "
        f"Breakdown by outcome: {', '.join([f'{k}: {len(v)}' for k,v in by_stance.items()])}."
        f"{conflict_note}"
    )

    return synthesis, limitations, final_position
