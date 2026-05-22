from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.lease_clause import LeaseClause
from app.schemas.lease_clause import (
    LeaseClauseCreate,
    LeaseClauseUpdate,
    LeaseClauseResponse,
    LeaseClauseListResponse,
)
from app.services.audit_service import audit_service
from app.services.clause_risk_scorer import scorer

router = APIRouter(prefix="/clauses", tags=["clauses"])


@router.post("", status_code=201, response_model=LeaseClauseResponse)
async def create_clause(
    clause_data: LeaseClauseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    clause = LeaseClause(**clause_data.model_dump())
    db.add(clause)
    await db.commit()
    await db.refresh(clause)

    await audit_service.log_action(
        db,
        "clause_created",
        "clause",
        str(clause.id),
        lease_id=clause.lease_id,
        user_id=current_user.id,
    )

    return clause


@router.get("/lease/{lease_id}", response_model=list[LeaseClauseListResponse])
async def list_clauses_by_lease(
    lease_id: uuid.UUID,
    clause_type: str | None = Query(None),
    min_risk: int = Query(0, ge=0, le=100),
    max_risk: int = Query(100, ge=0, le=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(LeaseClause).where(LeaseClause.lease_id == lease_id)

    if clause_type:
        query = query.where(LeaseClause.clause_type == clause_type)

    query = query.where(and_(LeaseClause.risk_score >= min_risk, LeaseClause.risk_score <= max_risk))

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{clause_id}", response_model=LeaseClauseResponse)
async def get_clause(
    clause_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(LeaseClause).where(LeaseClause.id == clause_id))
    clause = result.scalar_one_or_none()
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")
    return clause


@router.patch("/{clause_id}", response_model=LeaseClauseResponse)
async def update_clause(
    clause_id: uuid.UUID,
    clause_data: LeaseClauseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(LeaseClause).where(LeaseClause.id == clause_id))
    clause = result.scalar_one_or_none()
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")

    update_data = clause_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(clause, field, value)

    await db.commit()
    await db.refresh(clause)

    await audit_service.log_action(
        db,
        "clause_updated",
        "clause",
        str(clause.id),
        lease_id=clause.lease_id,
        user_id=current_user.id,
        changes=update_data,
    )

    return clause


@router.post("/{clause_id}/analyze")
async def analyze_clause(
    clause_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run AI risk analysis on a clause and update its scores."""
    result = await db.execute(select(LeaseClause).where(LeaseClause.id == clause_id))
    clause = result.scalar_one_or_none()
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")

    analysis = await scorer.score_clause(clause.clause_type, clause.extracted_text)

    from datetime import datetime, timezone
    clause.risk_score = analysis["risk_score"]
    clause.risk_factors = analysis["risk_factors"]
    clause.landlord_favorable = "true" if analysis["landlord_favorable"] else "false"
    clause.tenant_favorable = "true" if analysis["tenant_favorable"] else "false"
    clause.ai_summary = analysis.get("summary", "")
    clause.ai_recommendations = analysis.get("recommendations", [])
    clause.ai_analyzed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(clause)

    await audit_service.log_action(
        db, "clause_analyzed", "clause", str(clause.id),
        lease_id=clause.lease_id, user_id=current_user.id,
    )

    return {
        "clause_id": str(clause.id),
        "risk_score": clause.risk_score,
        "risk_factors": clause.risk_factors,
        "landlord_favorable": clause.landlord_favorable,
        "tenant_favorable": clause.tenant_favorable,
        "summary": clause.ai_summary,
        "recommendations": clause.ai_recommendations,
    }


@router.post("/lease/{lease_id}/analyze-all")
async def analyze_all_clauses(
    lease_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run AI risk analysis on all clauses for a lease."""
    import asyncio
    result = await db.execute(select(LeaseClause).where(LeaseClause.lease_id == lease_id))
    clauses = result.scalars().all()
    if not clauses:
        return {"analyzed": 0, "results": []}

    analyses = await asyncio.gather(*[scorer.score_clause(c.clause_type, c.extracted_text) for c in clauses])

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    results = []
    for clause, analysis in zip(clauses, analyses):
        clause.risk_score = analysis["risk_score"]
        clause.risk_factors = analysis["risk_factors"]
        clause.landlord_favorable = "true" if analysis["landlord_favorable"] else "false"
        clause.tenant_favorable = "true" if analysis["tenant_favorable"] else "false"
        clause.ai_summary = analysis.get("summary", "")
        clause.ai_recommendations = analysis.get("recommendations", [])
        clause.ai_analyzed_at = now
        results.append({
            "clause_id": str(clause.id),
            "clause_type": clause.clause_type,
            "risk_score": clause.risk_score,
            "risk_factors": clause.risk_factors,
            "summary": clause.ai_summary,
            "recommendations": clause.ai_recommendations,
        })

    await db.commit()
    return {"analyzed": len(clauses), "results": results}
