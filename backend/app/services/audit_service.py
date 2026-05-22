from __future__ import annotations
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Service for audit logging and compliance tracking."""

    async def log_action(
        self,
        db: AsyncSession,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        lease_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        changes: Optional[dict] = None,
    ) -> AuditLog:
        """Log an action to the audit trail."""
        audit_entry = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            lease_id=lease_id,
            user_id=user_id,
            changes=changes,
        )
        db.add(audit_entry)
        await db.commit()
        await db.refresh(audit_entry)
        logger.info(
            f"Audit: {action} on {entity_type}:{entity_id} by user {user_id}"
        )
        return audit_entry

    async def get_lease_audit_trail(
        self, db: AsyncSession, lease_id: UUID
    ) -> list[AuditLog]:
        """Get complete audit trail for a lease."""
        from sqlalchemy import select, desc

        result = await db.execute(
            select(AuditLog)
            .where(AuditLog.lease_id == lease_id)
            .order_by(desc(AuditLog.created_at))
        )
        return result.scalars().all()


audit_service = AuditService()
