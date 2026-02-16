"""
Arthronyx — Document Models

Pydantic schemas for orthopedic literature documents and their metadata.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import EvidenceLevel, OutcomeStance, StudyType, Subdomain


class DocumentMetadata(BaseModel):
    """Rich metadata for every indexed document."""
    doi: str = Field(..., description="Digital Object Identifier")
    title: str
    authors: List[str] = Field(default_factory=list)
    year: int
    journal: str = ""
    study_type: StudyType = StudyType.NARRATIVE_REVIEW
    evidence_level: EvidenceLevel = EvidenceLevel.LEVEL_V
    sample_size: Optional[int] = None
    subdomain: Subdomain = Subdomain.GENERAL
    country: str = ""
    trial_phase: Optional[str] = None
    abstract: str = ""
    source: str = Field(
        default="PubMed",
        description="Data source: PubMed, ClinicalTrials.gov, OpenAlex, AAOS, NICE, Cochrane"
    )


class DocumentChunk(BaseModel):
    """A single chunk of text from a document, ready for embedding."""
    chunk_id: str
    document_doi: str
    text: str
    chunk_index: int = 0
    embedding: Optional[List[float]] = None


class RetrievedDocument(BaseModel):
    """A document returned by the retrieval engine with scoring."""
    metadata: DocumentMetadata
    chunk_text: str
    semantic_score: float = 0.0
    evidence_weight: float = 0.0
    recency_score: float = 0.0
    final_score: float = 0.0
    outcome_stance: OutcomeStance = OutcomeStance.UNKNOWN


class DocumentIngest(BaseModel):
    """Request model for manual document ingestion."""
    doi: str
    title: str
    authors: List[str] = Field(default_factory=list)
    year: int
    journal: str = ""
    study_type: StudyType = StudyType.NARRATIVE_REVIEW
    evidence_level: EvidenceLevel = EvidenceLevel.LEVEL_V
    sample_size: Optional[int] = None
    subdomain: Subdomain = Subdomain.GENERAL
    country: str = ""
    trial_phase: Optional[str] = None
    abstract: str = ""
    full_text: str = ""
    source: str = "Manual"


class DocumentRecord(BaseModel):
    """Database record representation."""
    id: int
    doi: str
    title: str
    authors: List[str]
    year: int
    journal: str
    study_type: str
    evidence_level: str
    sample_size: Optional[int]
    subdomain: str
    country: str
    trial_phase: Optional[str]
    abstract: str
    source: str
    indexed_at: datetime
