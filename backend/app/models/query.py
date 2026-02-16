"""
Arthronyx — Query & Response Models

Structured schemas for the evidence synthesis pipeline I/O.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.enums import OutcomeStance, Subdomain


# ── Request ───────────────────────────────────────────────────

class QueryRequest(BaseModel):
    """Incoming evidence query."""
    query: str = Field(..., min_length=5, max_length=2000, description="Clinical question")
    subdomain_filter: Optional[Subdomain] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    study_types: Optional[List[str]] = None
    max_results: int = Field(default=10, ge=1, le=50)


# ── Evidence Overview ─────────────────────────────────────────

class StudyTypeDistribution(BaseModel):
    """Count of studies by type."""
    study_type: str
    count: int


class EvidenceOverview(BaseModel):
    """Summary statistics of retrieved evidence."""
    total_studies: int
    type_distribution: List[StudyTypeDistribution]
    year_range: str  # e.g. "2018–2024"
    subdomains_covered: List[str]


# ── Outcome Clusters ─────────────────────────────────────────

class ClusterStudy(BaseModel):
    """A study within an outcome cluster."""
    doi: str
    title: str
    year: int
    evidence_level: str
    sample_size: Optional[int]
    journal: str


class OutcomeCluster(BaseModel):
    """A cluster of studies grouped by outcome direction."""
    stance: OutcomeStance
    study_count: int
    total_sample_size: int
    avg_evidence_level: str
    studies: List[ClusterStudy]


# ── Conflict Report ──────────────────────────────────────────

class ConflictReport(BaseModel):
    """Explicit report of conflicting evidence."""
    has_conflict: bool
    clusters: List[OutcomeCluster]
    conflict_summary: str = ""


# ── Citation ─────────────────────────────────────────────────

class Citation(BaseModel):
    """An inline citation reference."""
    doi: str
    title: str
    authors_short: str  # e.g. "Smith et al."
    year: int
    journal: str


# ── Synthesis Result ─────────────────────────────────────────

class SynthesisResult(BaseModel):
    """Complete structured evidence synthesis — the mandatory 8-section output."""
    clinical_question: str
    evidence_overview: EvidenceOverview
    priority_evidence: List[Dict[str, str]]
    conflict_report: ConflictReport
    evidence_synthesis: str
    limitations: List[str]
    final_position: str
    disclaimer: str
    citations: List[Citation]
    validation_passed: bool = True


# ── Response ─────────────────────────────────────────────────

class QueryResponse(BaseModel):
    """Top-level API response for a query."""
    success: bool = True
    query_id: str
    result: Optional[SynthesisResult] = None
    error: Optional[str] = None
