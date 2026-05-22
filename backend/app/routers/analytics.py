from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.lease import CommercialLease
from app.models.lease_clause import LeaseClause
from app.models.obligation import Obligation
from app.models.critical_date import CriticalDate
from app.services.obligation_tracker import tracker
from app.config import get_settings
from datetime import date, timedelta

settings = get_settings()

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/portfolio/risk-summary")
async def get_portfolio_risk_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get portfolio-level risk summary by clause type."""
    result = await db.execute(
        select(
            LeaseClause.clause_type,
            func.avg(LeaseClause.risk_score).label("avg_risk_score"),
            func.count(LeaseClause.id).label("clause_count"),
        ).group_by(LeaseClause.clause_type)
    )
    rows = result.all()
    return {
        "summary": [
            {
                "clause_type": row[0],
                "avg_risk_score": float(row[1]) if row[1] else 0,
                "clause_count": row[2],
            }
            for row in rows
        ]
    }


@router.get("/portfolio/expiring-leases")
async def get_expiring_leases(
    days: int = Query(365, ge=1, le=3650),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get leases expiring within threshold days."""
    today = date.today()
    threshold_date = today + timedelta(days=days)
    result = await db.execute(
        select(CommercialLease).where(
            CommercialLease.term_end.between(today, threshold_date)
        )
    )
    leases = result.scalars().all()
    return {
        "expiring_count": len(leases),
        "leases": [
            {
                "id": str(lease.id),
                "tenant_name": lease.tenant_name,
                "property_address": lease.property_address,
                "term_end": lease.term_end,
                "days_until_expiry": (lease.term_end - today).days,
            }
            for lease in leases
        ],
    }


@router.get("/portfolio/obligation-compliance")
async def get_obligation_compliance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get overall obligation compliance rate."""
    compliance = await tracker.get_compliance_rate(db)
    overdue = await tracker.get_overdue_obligations(db)
    upcoming = await tracker.get_upcoming_obligations(db, days_threshold=30)

    return {
        "total_obligations": compliance["total"],
        "completed": compliance["completed"],
        "compliance_rate": round(compliance["rate"], 2),
        "overdue_count": len(overdue),
        "upcoming_30_days": len(upcoming),
    }


@router.get("/lease/{lease_id}/risk-breakdown")
async def get_lease_risk_breakdown(
    lease_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed risk breakdown for a single lease."""
    result = await db.execute(
        select(LeaseClause).where(LeaseClause.lease_id == lease_id)
    )
    clauses = result.scalars().all()

    if not clauses:
        return {"lease_id": str(lease_id), "total_clauses": 0, "avg_risk": 0, "clauses": []}

    total_risk = sum(c.risk_score for c in clauses)
    avg_risk = total_risk / len(clauses) if clauses else 0

    high_risk = [c for c in clauses if c.risk_score >= settings.CLAUSE_RISK_HIGH_THRESHOLD]
    medium_risk = [c for c in clauses if settings.CLAUSE_RISK_MEDIUM_THRESHOLD <= c.risk_score < settings.CLAUSE_RISK_HIGH_THRESHOLD]
    low_risk = [c for c in clauses if c.risk_score < settings.CLAUSE_RISK_MEDIUM_THRESHOLD]

    return {
        "lease_id": str(lease_id),
        "total_clauses": len(clauses),
        "avg_risk_score": round(avg_risk, 2),
        "high_risk_count": len(high_risk),
        "medium_risk_count": len(medium_risk),
        "low_risk_count": len(low_risk),
        "clauses": [
            {
                "id": str(c.id),
                "clause_type": c.clause_type,
                "risk_score": c.risk_score,
                "landlord_favorable": c.landlord_favorable,
                "tenant_favorable": c.tenant_favorable,
            }
            for c in clauses
        ],
    }


@router.get("/portfolio/lease-status-distribution")
async def get_lease_status_distribution(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get count of leases by status."""
    result = await db.execute(
        select(CommercialLease.status, func.count(CommercialLease.id)).group_by(
            CommercialLease.status
        )
    )
    rows = result.all()
    return {
        "distribution": [{"status": row[0], "count": row[1]} for row in rows]
    }
