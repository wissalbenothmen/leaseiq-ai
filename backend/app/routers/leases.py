from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.lease import CommercialLease
from app.schemas.lease import (
    CommercialLeaseCreate,
    CommercialLeaseUpdate,
    CommercialLeaseResponse,
    CommercialLeaseListResponse,
)
from app.services.audit_service import audit_service
from app.services.clause_risk_scorer import scorer
from app.models.lease_clause import LeaseClause
from app.models.critical_date import CriticalDate
from app.models.obligation import Obligation
from app.models.lease_document import LeaseDocument
from app.models.clause_query import ClauseQuery
from app.services.lease_clause_analyzer import LeaseClauseAnalyzer
from app.services.tenant_briefing_pdf_service import (
    render_tenant_briefing_pdf,
    safe_pdf_filename,
)

router = APIRouter(prefix="/leases", tags=["leases"])


@router.post("", status_code=201, response_model=CommercialLeaseResponse)
async def create_lease(
    lease_data: CommercialLeaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lease = CommercialLease(
        **lease_data.model_dump(),
        created_by=current_user.id,
    )
    db.add(lease)
    await db.commit()
    await db.refresh(lease)

    await audit_service.log_action(
        db,
        "lease_created",
        "lease",
        str(lease.id),
        lease_id=lease.id,
        user_id=current_user.id,
    )

    return lease


@router.get("", response_model=list[CommercialLeaseListResponse])
async def list_leases(
    status: str | None = Query(None),
    tenant_name: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(CommercialLease)

    if status:
        query = query.where(CommercialLease.status == status)
    if tenant_name:
        query = query.where(CommercialLease.tenant_name.ilike(f"%{tenant_name}%"))

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{lease_id}", response_model=CommercialLeaseResponse)
async def get_lease(
    lease_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CommercialLease).where(CommercialLease.id == lease_id))
    lease = result.scalar_one_or_none()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")
    return lease


@router.patch("/{lease_id}", response_model=CommercialLeaseResponse)
async def update_lease(
    lease_id: uuid.UUID,
    lease_data: CommercialLeaseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CommercialLease).where(CommercialLease.id == lease_id))
    lease = result.scalar_one_or_none()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    update_data = lease_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lease, field, value)

    await db.commit()
    await db.refresh(lease)

    await audit_service.log_action(
        db,
        "lease_updated",
        "lease",
        str(lease.id),
        lease_id=lease.id,
        user_id=current_user.id,
        changes=update_data,
    )

    return lease


@router.delete("/{lease_id}", status_code=204)
async def delete_lease(
    lease_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CommercialLease).where(CommercialLease.id == lease_id))
    lease = result.scalar_one_or_none()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    await db.delete(lease)
    await db.commit()

    await audit_service.log_action(
        db,
        "lease_deleted",
        "lease",
        str(lease_id),
        lease_id=None,
        user_id=current_user.id,
        changes={"deleted_lease_id": str(lease_id)},
    )


@router.get("/{lease_id}/detail")
async def get_lease_detail(
    lease_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full lease detail including clauses, obligations and critical dates."""
    result = await db.execute(select(CommercialLease).where(CommercialLease.id == lease_id))
    lease = result.scalar_one_or_none()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    clauses_result = await db.execute(select(LeaseClause).where(LeaseClause.lease_id == lease_id))
    clauses = clauses_result.scalars().all()

    obligations_result = await db.execute(select(Obligation).where(Obligation.lease_id == lease_id))
    obligations = obligations_result.scalars().all()

    dates_result = await db.execute(select(CriticalDate).where(CriticalDate.lease_id == lease_id))
    critical_dates = dates_result.scalars().all()

    avg_risk = sum(c.risk_score for c in clauses) / len(clauses) if clauses else 0

    return {
        "lease": {
            "id": str(lease.id),
            "property_address": lease.property_address,
            "tenant_name": lease.tenant_name,
            "landlord_name": lease.landlord_name,
            "lease_type": lease.lease_type,
            "term_start": lease.term_start,
            "term_end": lease.term_end,
            "base_rent": float(lease.base_rent) if lease.base_rent else None,
            "rent_escalation_pct": float(lease.rent_escalation_pct) if lease.rent_escalation_pct else None,
            "status": lease.status,
            "suite_number": lease.suite_number,
            "square_footage": float(lease.square_footage) if lease.square_footage else None,
            "notes": lease.notes,
        },
        "clauses": [
            {
                "id": str(c.id),
                "clause_type": c.clause_type,
                "extracted_text": c.extracted_text,
                "risk_score": c.risk_score,
                "risk_factors": c.risk_factors,
                "landlord_favorable": c.landlord_favorable,
                "tenant_favorable": c.tenant_favorable,
                "confidence_score": c.confidence_score,
                "ai_summary": c.ai_summary,
                "ai_recommendations": c.ai_recommendations,
                "ai_analyzed_at": c.ai_analyzed_at,
            }
            for c in clauses
        ],
        "obligations": [
            {
                "id": str(o.id),
                "obligation_type": o.obligation_type,
                "due_date": o.due_date,
                "status": o.status,
                "amount": float(o.amount) if o.amount else None,
                "responsible_party": o.responsible_party,
                "recurrence": o.recurrence,
            }
            for o in obligations
        ],
        "critical_dates": [
            {
                "id": str(d.id),
                "date_type": d.date_type,
                "date_value": d.date_value,
                "days_until": d.days_until,
                "alert_sent": d.alert_sent,
            }
            for d in critical_dates
        ],
        "summary": {
            "clause_count": len(clauses),
            "avg_risk_score": round(avg_risk, 1),
            "high_risk_clauses": sum(1 for c in clauses if c.risk_score >= 70),
            "overdue_obligations": sum(1 for o in obligations if o.status == "overdue"),
            "upcoming_dates": sum(1 for d in critical_dates if 0 <= (d.days_until or 999) <= 90),
        },
    }


# ===== Phase B + C — voice clause-query ↔ lease cross-validation + tenant briefing PDF =====

async def _gather_briefing(lease_id: uuid.UUID, db: AsyncSession):
    lease_q = await db.execute(
        select(CommercialLease).where(CommercialLease.id == lease_id)
    )
    lease = lease_q.scalar_one_or_none()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    # Latest voice clause-query → transcript
    cq_q = await db.execute(
        select(ClauseQuery)
        .where(ClauseQuery.lease_id == lease_id)
        .order_by(ClauseQuery.created_at.desc())
    )
    latest_cq = cq_q.scalars().first()
    transcript = (latest_cq.voice_transcript if latest_cq else "") or ""

    # Extracted clauses for this lease
    cl_q = await db.execute(
        select(LeaseClause).where(LeaseClause.lease_id == lease_id)
    )
    clauses = cl_q.scalars().all()
    clause_tuples = [(c.id, c.clause_type or "clause", c.extracted_text or "") for c in clauses]

    # Lease documents for OCR enrichment
    doc_q = await db.execute(
        select(LeaseDocument).where(LeaseDocument.lease_id == lease_id)
    )
    docs = doc_q.scalars().all()
    doc_tuples = [(d.id, d.filename, d.ocr_text or "") for d in docs]

    analyzer = LeaseClauseAnalyzer()
    result = await analyzer.analyze(transcript, clause_tuples, doc_tuples)
    return lease, transcript, clauses, docs, result


@router.post("/{lease_id}/cross-validate-voice")
async def cross_validate_voice(
    lease_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Phase B — cross-check the latest voice clause-query against the lease's
    extracted clauses + supporting document OCR. Returns topics, matches,
    conflicts, ambiguities, talking points."""
    lease, transcript, clauses, docs, result = await _gather_briefing(lease_id, db)
    return {
        "status": "completed" if transcript else "no_transcript",
        "mode": result.get("mode"),
        "lease_id": str(lease_id),
        "transcript_excerpt": transcript[:500],
        "clauses_checked": len(clauses),
        "documents_checked": len(docs),
        "topics": result.get("topics", {}),
        "matches": result.get("matches", []),
        "conflicts": result.get("conflicts", []),
        "ambiguities": result.get("ambiguities", []),
        "talking_points": result.get("talking_points", []),
        "plain_language_answer": result.get("plain_language_answer"),
    }


@router.get("/{lease_id}/tenant-briefing.pdf")
async def generate_tenant_briefing_pdf(
    lease_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Phase C — render the tenant-briefing PDF."""
    lease, transcript, clauses, docs, result = await _gather_briefing(lease_id, db)
    pdf_bytes = render_tenant_briefing_pdf(
        lease={
            "property_address": lease.property_address,
            "tenant_name": lease.tenant_name,
            "landlord_name": lease.landlord_name,
            "lease_type": lease.lease_type,
            "status": lease.status,
        },
        transcript=transcript or None,
        topics=result.get("topics", {}),
        matches=result.get("matches", []),
        conflicts=result.get("conflicts", []),
        ambiguities=result.get("ambiguities", []),
        talking_points=result.get("talking_points", []),
        plain_language_answer=result.get("plain_language_answer"),
        generated_by=getattr(current_user, "email", None) or str(current_user.id),
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_pdf_filename(lease.tenant_name or str(lease.id))}"',
            "X-LeaseIQ-Conflicts": str(len(result.get("conflicts", []))),
            "X-LeaseIQ-Ambiguities": str(len(result.get("ambiguities", []))),
            "X-LeaseIQ-Mode": result.get("mode", "unknown"),
        },
    )
