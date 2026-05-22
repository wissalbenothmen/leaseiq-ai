from __future__ import annotations
import logging
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.obligation import Obligation

logger = logging.getLogger(__name__)


class ObligationTracker:
    """Service to track obligations and identify overdue items."""

    async def get_overdue_obligations(self, db: AsyncSession, lease_id=None) -> list[Obligation]:
        """Get all overdue obligations."""
        today = date.today()
        query = select(Obligation).where(
            and_(
                Obligation.status.in_(["pending", "overdue"]),
                Obligation.due_date < today,
            )
        )
        if lease_id:
            query = query.where(Obligation.lease_id == lease_id)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_upcoming_obligations(
        self, db: AsyncSession, days_threshold: int = 30, lease_id=None
    ) -> list[Obligation]:
        """Get obligations due within threshold days."""
        today = date.today()
        threshold_date = today + timedelta(days=days_threshold)
        query = select(Obligation).where(
            and_(
                Obligation.status == "pending",
                Obligation.due_date >= today,
                Obligation.due_date <= threshold_date,
            )
        )
        if lease_id:
            query = query.where(Obligation.lease_id == lease_id)
        result = await db.execute(query)
        return result.scalars().all()

    async def mark_obligation_completed(self, db: AsyncSession, obligation_id) -> Obligation:
        """Mark an obligation as completed."""
        result = await db.execute(select(Obligation).where(Obligation.id == obligation_id))
        obligation = result.scalar_one_or_none()
        if obligation:
            obligation.status = "completed"
            obligation.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await db.commit()
            await db.refresh(obligation)
        return obligation

    async def get_compliance_rate(self, db: AsyncSession, lease_id=None) -> dict:
        """Calculate obligation compliance rate."""
        query_all = select(Obligation)
        query_completed = select(Obligation).where(Obligation.status == "completed")
        if lease_id:
            query_all = query_all.where(Obligation.lease_id == lease_id)
            query_completed = query_completed.where(Obligation.lease_id == lease_id)

        result_all = await db.execute(query_all)
        all_obligations = result_all.scalars().all()

        result_completed = await db.execute(query_completed)
        completed = result_completed.scalars().all()

        total = len(all_obligations)
        completed_count = len(completed)
        rate = (completed_count / total * 100) if total > 0 else 0

        return {"total": total, "completed": completed_count, "rate": rate}


tracker = ObligationTracker()
