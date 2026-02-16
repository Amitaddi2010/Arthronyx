"""
Arthronyx — Medico-Legal Disclaimer

Mandatory disclaimer appended to every synthesis output.
"""

DISCLAIMER = (
    "This output is an evidence summary based on retrieved scientific literature. "
    "It is not medical advice and should not be used as a substitute for qualified "
    "clinical judgment. The information presented reflects the state of the retrieved "
    "corpus and may not represent the entirety of available evidence. No personalized "
    "treatment recommendations or patient-specific advice is provided. Clinical decisions "
    "should always be made by qualified healthcare professionals considering individual "
    "patient circumstances."
)


def get_disclaimer() -> str:
    """Return the mandatory medico-legal disclaimer."""
    return DISCLAIMER
