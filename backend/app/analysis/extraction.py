"""
Arthronyx — Metadata Extraction Utilities

Extracts structured data from unstructured text using regex and heuristics.
Target fields: Sample Size, Study Type (Refined), Follow-up Duration.
"""

import re
from typing import Any, Dict, Optional

import structlog

logger = structlog.get_logger(__name__)

# Pattern to find sample size (N)
# Matches: "n = 123", "N=123", "123 patients", "123 hips", "123 knees"
SAMPLE_SIZE_PATTERNS = [
    r"\b[nN]\s*=\s*(\d+)",
    r"(\d+)\s+patients",
    r"(\d+)\s+participants",
    r"(\d+)\s+hips",
    r"(\d+)\s+knees",
    r"(\d+)\s+cases",
    r"group of (\d+)",
    r"total of (\d+)",
]

def extract_sample_size(text: str) -> int:
    """Extract sample size from abstract text."""
    if not text:
        return 0
    
    text_lower = text.lower()
    
    # Try all patterns
    matches = []
    for pattern in SAMPLE_SIZE_PATTERNS:
        found = re.findall(pattern, text_lower)
        for val in found:
            try:
                num = int(val)
                # Filter out likely years or unlikely small/large numbers
                if 5 <= num <= 1000000 and num != 2024 and num != 2025:
                    matches.append(num)
            except ValueError:
                pass
    
    # Return the largest reasonable number found (often N=Total is mentioned last or explicitly)
    # But usually "N=..." is the most reliable if present.
    
    # Prioritize "n=" explicit matches first
    n_equals = re.findall(r"\b[nN]\s*=\s*(\d+)", text)
    if n_equals:
        try:
            return int(n_equals[0])
        except:
            pass
            
    return max(matches) if matches else 0


def refine_evidence_level(text: str, current_level: str = "V") -> str:
    """Refine evidence level based on abstract keywords."""
    text_lower = text.lower()
    
    # Level I: Meta-analyses, Systematic Reviews
    if "meta-analysis" in text_lower or "systematic review" in text_lower:
        return "I"
        
    # Level II: RCTs
    if "randomized" in text_lower or "randomised" in text_lower:
        return "II"
    
    # Level III: Cohort, Case-Control
    if "cohort" in text_lower or "case-control" in text_lower or "retrospective review" in text_lower:
        if current_level in ["IV", "V"]:
            return "III"
            
    # Level IV: Case series
    if "case series" in text_lower:
        return "IV"
        
    return current_level


def extract_metadata(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance document with extracted metadata."""
    text = doc.get("text", "") or doc.get("abstract", "")
    
    # 1. Sample Size
    if not doc.get("sample_size"):
        doc["sample_size"] = extract_sample_size(text)
        
    # 2. Refine Evidence Level
    doc["evidence_level"] = refine_evidence_level(text, doc.get("evidence_level", "V"))
    
    return doc
