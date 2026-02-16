"""
Arthronyx — FastAPI Application Entry Point

Evidence-Structured Orthopedic Intelligence Engine.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import audit, citation_graph, health, ingest, query
from app.config import settings
from app.middleware.audit import AuditMiddleware
from app.middleware.safety import SafetyMiddleware

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle: startup & shutdown."""
    logger.info("arthronyx.startup", version="1.0.0")

    # ── Startup: attempt database connections (non-fatal) ─────
    try:
        from app.db.postgres import init_db
        await init_db()
        logger.info("arthronyx.postgres_ready")
    except Exception as e:
        logger.warning("arthronyx.postgres_unavailable", error=str(e))

    try:
        from app.db.qdrant import init_qdrant
        await init_qdrant()
        logger.info("arthronyx.qdrant_ready")
    except Exception as e:
        logger.warning("arthronyx.qdrant_unavailable", error=str(e))

    logger.info("arthronyx.startup_complete")

    yield

    # ── Shutdown: close connections ───────────────────────────
    try:
        from app.db.neo4j import neo4j_driver
        await neo4j_driver.close()
    except Exception:
        pass
    logger.info("arthronyx.shutdown_complete")


app = FastAPI(
    title="Arthronyx",
    description=(
        "Evidence-Structured Orthopedic Intelligence Engine. "
        "Citation-grounded, conflict-aware, time-weighted evidence synthesis."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Custom Middleware ─────────────────────────────────────────
app.add_middleware(AuditMiddleware)
app.add_middleware(SafetyMiddleware)

# ── Route Registration ────────────────────────────────────────
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(query.router, prefix="/api/v1", tags=["Query"])
app.include_router(ingest.router, prefix="/api/v1", tags=["Ingestion"])
app.include_router(citation_graph.router, prefix="/api/v1", tags=["Citation Graph"])
app.include_router(audit.router, prefix="/api/v1", tags=["Audit"])
