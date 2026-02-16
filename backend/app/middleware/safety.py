"""
Arthronyx — Safety Middleware

Prevents personalized treatment recommendations and patient-specific advice.
Screens incoming queries for safety violations.
"""

import re
from typing import Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = structlog.get_logger(__name__)

# Patterns that suggest patient-specific or treatment-recommendation queries
UNSAFE_PATTERNS = [
    r"\b(?:my|i|me|my\s+patient)\s+(?:have|has|am|was|had)\b",
    r"\bshould\s+(?:i|my\s+patient|the\s+patient)\s+(?:take|use|get|undergo)\b",
    r"\bprescribe\b",
    r"\bwhat\s+(?:medication|drug|dose|dosage)\s+should\b",
    r"\btreat(?:ment)?\s+(?:plan|protocol)\s+for\s+(?:me|my|this\s+patient)\b",
    r"\bdiagnos(?:e|is)\s+(?:me|my)\b",
    r"\b(?:age|weight|height|bmi)\s*[:=]\s*\d+\b",
    r"\bpatient\s+(?:name|id|mrn)\b",
]

SAFETY_RESPONSE = {
    "success": False,
    "error": (
        "This query appears to request personalized medical advice or patient-specific "
        "treatment recommendations. Arthronyx is an evidence synthesis engine and cannot "
        "provide individualized clinical guidance. Please rephrase your query as a general "
        "clinical question about orthopedic evidence."
    ),
}


class SafetyMiddleware(BaseHTTPMiddleware):
    """Middleware that blocks queries requesting personalized medical advice."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only check query endpoints
        if request.method == "POST" and "/query" in request.url.path:
            try:
                body = await request.body()
                body_text = body.decode("utf-8", errors="ignore").lower()

                for pattern in UNSAFE_PATTERNS:
                    if re.search(pattern, body_text, re.IGNORECASE):
                        logger.warning(
                            "safety.blocked_query",
                            pattern=pattern,
                            client_ip=request.client.host if request.client else "unknown",
                        )
                        return JSONResponse(
                            status_code=422,
                            content=SAFETY_RESPONSE,
                        )
            except Exception as e:
                logger.error("safety.middleware_error", error=str(e))
                # Don't block on middleware errors — let the request through

        return await call_next(request)
