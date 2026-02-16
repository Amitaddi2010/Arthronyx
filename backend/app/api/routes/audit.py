"""
Arthronyx — Audit Trail Endpoint

Read-only access to query audit logs.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import AuditLogORM, get_db

router = APIRouter()


@router.get("/audit", response_model=List[Dict[str, Any]])
async def get_audit_logs(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve audit logs (admin only)."""
    # In production, add auth/admin check here
    query = (
        select(AuditLogORM)
        .order_by(AuditLogORM.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        {
            "id": log.id,
            "query_id": log.query_id,
            "query_text": log.query_text,
            "retrieved_count": len(log.retrieved_dois) if log.retrieved_dois else 0,
            "validation_passed": log.validation_pass,
            "processing_ms": log.processing_ms,
            "created_at": log.created_at,
        }
        for log in logs
    ]
