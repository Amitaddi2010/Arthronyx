"""
Arthronyx — Enumeration Types

Study types, evidence levels, subdomains, and outcome stances.
"""

from enum import Enum


class StudyType(str, Enum):
    """Classifies the study design of a document."""
    GUIDELINE = "Guideline"
    META_ANALYSIS = "Meta-analysis"
    SYSTEMATIC_REVIEW = "Systematic Review"
    RCT = "RCT"
    COHORT = "Cohort"
    CASE_CONTROL = "Case-Control"
    CROSS_SECTIONAL = "Cross-Sectional"
    CASE_SERIES = "Case Series"
    CASE_REPORT = "Case Report"
    EXPERT_OPINION = "Expert Opinion"
    NARRATIVE_REVIEW = "Narrative Review"


class EvidenceLevel(str, Enum):
    """Oxford Centre for Evidence-Based Medicine levels."""
    LEVEL_I = "I"
    LEVEL_II = "II"
    LEVEL_III = "III"
    LEVEL_IV = "IV"
    LEVEL_V = "V"


# Numerical weight for sorting — higher = stronger evidence
EVIDENCE_LEVEL_WEIGHT: dict[str, float] = {
    EvidenceLevel.LEVEL_I: 1.0,
    EvidenceLevel.LEVEL_II: 0.8,
    EvidenceLevel.LEVEL_III: 0.6,
    EvidenceLevel.LEVEL_IV: 0.4,
    EvidenceLevel.LEVEL_V: 0.2,
}

# Study-type to default evidence level mapping
STUDY_TYPE_EVIDENCE_MAP: dict[str, EvidenceLevel] = {
    StudyType.GUIDELINE: EvidenceLevel.LEVEL_I,
    StudyType.META_ANALYSIS: EvidenceLevel.LEVEL_I,
    StudyType.SYSTEMATIC_REVIEW: EvidenceLevel.LEVEL_I,
    StudyType.RCT: EvidenceLevel.LEVEL_II,
    StudyType.COHORT: EvidenceLevel.LEVEL_III,
    StudyType.CASE_CONTROL: EvidenceLevel.LEVEL_III,
    StudyType.CROSS_SECTIONAL: EvidenceLevel.LEVEL_IV,
    StudyType.CASE_SERIES: EvidenceLevel.LEVEL_IV,
    StudyType.CASE_REPORT: EvidenceLevel.LEVEL_V,
    StudyType.EXPERT_OPINION: EvidenceLevel.LEVEL_V,
    StudyType.NARRATIVE_REVIEW: EvidenceLevel.LEVEL_V,
}


class Subdomain(str, Enum):
    """Orthopedic sub-specialties."""
    ARTHROPLASTY = "Arthroplasty"
    SPINE = "Spine"
    TRAUMA = "Trauma"
    SPORTS = "Sports Medicine"
    PEDIATRIC = "Pediatric Orthopedics"
    FOOT_ANKLE = "Foot & Ankle"
    HAND_UPPER_EXTREMITY = "Hand & Upper Extremity"
    ONCOLOGY = "Musculoskeletal Oncology"
    GENERAL = "General Orthopedics"


class OutcomeStance(str, Enum):
    """Extracted outcome direction of a study."""
    POSITIVE = "Positive Effect"
    NEGATIVE = "Negative Effect"
    NO_SIGNIFICANT_DIFFERENCE = "No Significant Difference"
    MIXED = "Mixed"
    UNKNOWN = "Unknown"
