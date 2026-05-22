from __future__ import annotations
import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.obligation import Obligation
from app.schemas.obligation import (
    ObligationCreate,
    ObligationUpdate,
    ObligationResponse,
    ObligationListResponse,
)
from app.services.obligation_tracker import tracker
from app.services.audit_service import audit_service


async def _auto_update_overdue(db: AsyncSession, obligations: list[Obligation]) -> list[Obligation]:
    """Auto-transition 'pending' obligations to 'overdue' when past due_date."""
    today = date.today()
    updated = False
    for o in obligations:
        if o.status == "pending" and o.due_date < today:
            o.status = "overdue"
            updated = True
    if updated:
        await db.commit()
    return obligations

router = APIRouter(prefix="/obligations", tags=["obligations"])


@router.post("", status_code=201, response_model=ObligationResponse)
async def create_obligation(
    obligation_data: ObligationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    obligation = Obligation(**obligation_data.model_dump())
    db.add(obligation)
    await db.commit()
    await db.refresh(obligation)

    await audit_service.log_action(
        db,
        "obligation_created",
        "obligation",
        str(obligation.id),
        lease_id=obligation.lease_id,
        user_id=current_user.id,
    )

    return obligation


@router.get("/lease/{lease_id}", response_model=list[ObligationListResponse])
async def list_obligations_by_lease(
    lease_id: uuid.UUID,
    status: str | None = Query(None),
    obligation_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Obligation).where(Obligation.lease_id == lease_id)

    if obligation_type:
        query = query.where(Obligation.obligation_type == obligation_type)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    obligations = result.scalars().all()
    obligations = await _auto_update_overdue(db, list(obligations))

    if status:
        obligations = [o for o in obligations if o.status == status]

    return obligations


@router.get("/overdue", response_model=list[ObligationListResponse])
async def get_overdue_obligations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # First auto-transition any stale pending obligations
    all_pending = await db.execute(
        select(Obligation).where(Obligation.status == "pending")
    )
    await _auto_update_overdue(db, list(all_pending.scalars().all()))
    return await tracker.get_overdue_obligations(db)


@router.get("/upcoming", response_model=list[ObligationListResponse])
async def get_upcoming_obligations(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await tracker.get_upcoming_obligations(db, days_threshold=days)


@router.get("/{obligation_id}", response_model=ObligationResponse)
async def get_obligation(
    obligation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Obligation).where(Obligation.id == obligation_id))
    obligation = result.scalar_one_or_none()
    if not obligation:
        raise HTTPException(status_code=404, detail="Obligation not found")
    return obligation


@router.patch("/{obligation_id}", response_model=ObligationResponse)
async def update_obligation(
    obligation_id: uuid.UUID,
    obligation_data: ObligationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Obligation).where(Obligation.id == obligation_id))
    obligation = result.scalar_one_or_none()
    if not obligation:
        raise HTTPException(status_code=404, detail="Obligation not found")

    update_data = obligation_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(obligation, field, value)

    await db.commit()
    await db.refresh(obligation)

    await audit_service.log_action(
        db,
        "obligation_updated",
        "obligation",
        str(obligation.id),
        lease_id=obligation.lease_id,
        user_id=current_user.id,
        changes=update_data,
    )

    return obligation


@router.post("/{obligation_id}/complete", response_model=ObligationResponse)
async def mark_obligation_complete(
    obligation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    obligation = await tracker.mark_obligation_completed(db, obligation_id)
    if not obligation:
        raise HTTPException(status_code=404, detail="Obligation not found")

    await audit_service.log_action(
        db,
        "obligation_completed",
        "obligation",
        str(obligation.id),
        lease_id=obligation.lease_id,
        user_id=current_user.id,
    )

    return obligation
