from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.critical_date import CriticalDate
from app.schemas.critical_date import (
    CriticalDateCreate,
    CriticalDateUpdate,
    CriticalDateResponse,
    CriticalDateListResponse,
)
from app.services.critical_date_extractor import extractor
from app.services.audit_service import audit_service

router = APIRouter(prefix="/critical-dates", tags=["critical-dates"])


@router.post("", status_code=201, response_model=CriticalDateResponse)
async def create_critical_date(
    date_data: CriticalDateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    critical_date = CriticalDate(**date_data.model_dump())
    critical_date.days_until = extractor.calculate_days_until(critical_date.date_value)
    db.add(critical_date)
    await db.commit()
    await db.refresh(critical_date)

    await audit_service.log_action(
        db,
        "critical_date_created",
        "critical_date",
        str(critical_date.id),
        lease_id=critical_date.lease_id,
        user_id=current_user.id,
    )

    return critical_date


@router.get("/lease/{lease_id}", response_model=list[CriticalDateListResponse])
async def list_dates_by_lease(
    lease_id: uuid.UUID,
    date_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(CriticalDate).where(CriticalDate.lease_id == lease_id)

    if date_type:
        query = query.where(CriticalDate.date_type == date_type)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/upcoming/portfolio", response_model=list[CriticalDateListResponse])
async def get_upcoming_dates(
    days: int = Query(90, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date, timedelta

    today = date.today()
    threshold_date = today + timedelta(days=days)
    result = await db.execute(
        select(CriticalDate).where(
            and_(
                CriticalDate.date_value >= today,
                CriticalDate.date_value <= threshold_date,
            )
        )
    )
    return result.scalars().all()


@router.get("/{critical_date_id}", response_model=CriticalDateResponse)
async def get_critical_date(
    critical_date_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CriticalDate).where(CriticalDate.id == critical_date_id)
    )
    critical_date = result.scalar_one_or_none()
    if not critical_date:
        raise HTTPException(status_code=404, detail="Critical date not found")
    return critical_date


@router.patch("/{critical_date_id}", response_model=CriticalDateResponse)
async def update_critical_date(
    critical_date_id: uuid.UUID,
    date_data: CriticalDateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CriticalDate).where(CriticalDate.id == critical_date_id)
    )
    critical_date = result.scalar_one_or_none()
    if not critical_date:
        raise HTTPException(status_code=404, detail="Critical date not found")

    update_data = date_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(critical_date, field, value)

    await db.commit()
    await db.refresh(critical_date)

    await audit_service.log_action(
        db,
        "critical_date_updated",
        "critical_date",
        str(critical_date.id),
        lease_id=critical_date.lease_id,
        user_id=current_user.id,
        changes=update_data,
    )

    return critical_date
