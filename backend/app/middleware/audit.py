"""
Arthronyx — Audit Logging Middleware

Logs all incoming queries and outgoing responses for medico-legal audit trail.
"""

import time
import uuid
from typing import Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware that logs every request/response for audit purposes."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.start_time = time.time()

        try:
            # Log request
            logger.info(
                "audit.request",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                client_ip=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("user-agent", ""),
            )

            # Process request
            response = await call_next(request)

            # Calculate processing time
            elapsed_ms = int((time.time() - request.state.start_time) * 1000)

            # Log response
            logger.info(
                "audit.response",
                request_id=request_id,
                status_code=response.status_code,
                processing_ms=elapsed_ms,
            )

            # Add audit headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Processing-Time-Ms"] = str(elapsed_ms)

            return response

        except Exception as e:
            # Calculate processing time for error case
            elapsed_ms = int((time.time() - request.state.start_time) * 1000)
            
            logger.error(
                "audit.error",
                request_id=request_id,
                error=str(e),
                processing_ms=elapsed_ms,
            )
            
            from starlette.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"},
                headers={
                    "X-Request-ID": request_id,
                    "X-Processing-Time-Ms": str(elapsed_ms),
                },
            )
