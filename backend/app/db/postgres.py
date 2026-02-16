"""
Arthronyx — PostgreSQL Database Layer

Async SQLAlchemy engine, session management, and ORM models.
"""

from typing import AsyncGenerator

import structlog
from sqlalchemy import (
    ARRAY,
    TIMESTAMP,
    Boolean,
    Column,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = structlog.get_logger(__name__)


# ── Engine & Session Factory ──────────────────────────────────

engine = create_async_engine(
    settings.postgres_dsn,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Verify database connectivity on startup."""
    async with engine.begin() as conn:
        await conn.execute(func.now())
    logger.info("postgres.connected", dsn=settings.postgres_host)


# ── ORM Base ─────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── ORM Models ───────────────────────────────────────────────

class DocumentORM(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doi = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False)
    authors = Column(ARRAY(Text), default=[])
    year = Column(Integer, nullable=False)
    journal = Column(String(500), default="")
    study_type = Column(String(100), nullable=False, default="Narrative Review")
    evidence_level = Column(String(10), nullable=False, default="V")
    sample_size = Column(Integer, nullable=True)
    subdomain = Column(String(100), default="General Orthopedics")
    country = Column(String(100), default="")
    trial_phase = Column(String(50), nullable=True)
    abstract = Column(Text, default="")
    full_text_hash = Column(String(64), nullable=True)
    source = Column(String(100), nullable=False, default="PubMed")
    indexed_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class DocumentChunkORM(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_id = Column(String(255), unique=True, nullable=False)
    document_doi = Column(String(255), nullable=False, index=True)
    chunk_index = Column(Integer, default=0)
    text = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class AuditLogORM(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_id = Column(String(100), unique=True, nullable=False)
    query_text = Column(Text, nullable=False)
    query_filters = Column(JSONB, default={})
    response_json = Column(JSONB, nullable=True)
    retrieved_dois = Column(ARRAY(Text), default=[])
    cited_dois = Column(ARRAY(Text), default=[])
    validation_pass = Column(Boolean, default=True)
    client_ip = Column(String(45), default="")
    user_agent = Column(Text, default="")
    processing_ms = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class IngestionLogORM(Base):
    __tablename__ = "ingestion_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(100), nullable=False)
    query_used = Column(Text, default="")
    documents_found = Column(Integer, default=0)
    documents_added = Column(Integer, default=0)
    errors = Column(Text, default="")
    started_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
