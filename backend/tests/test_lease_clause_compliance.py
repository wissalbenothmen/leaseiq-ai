"""Phase B + C tests for LeaseIQ — voice clause-query ↔ clause cross-validation + tenant-briefing PDF."""
from __future__ import annotations

import os
import uuid

import pytest
from datetime import date


@pytest.fixture(autouse=True)
def _mock_fraud_gpt():
    os.environ["MOCK_FRAUD_GPT"] = "true"
    yield
    os.environ.pop("MOCK_FRAUD_GPT", None)


@pytest.mark.asyncio
async def test_topic_detector_and_conflicts():
    from app.services.lease_clause_analyzer import (
        detect_topics, LeaseClauseAnalyzer,
    )
    transcript = (
        "I want to assign the lease to a related entity next quarter and also "
        "trigger the renewal option. Does the renewal window line up with the "
        "30-day notice we read in section 5?"
    )
    topics = detect_topics(transcript)
    assert "assignment" in topics
    assert "renewal" in topics

    # Two clauses that disagree on the renewal notice window — should surface a conflict.
    clauses = [
        (
            uuid.uuid4(),
            "renewal_option",
            "Tenant may exercise the renewal option by giving 30 days written notice prior to the expiration date.",
        ),
        (
            uuid.uuid4(),
            "renewal_option_reaffirmation",
            "Tenant shall provide ninety (90) days notice to renew the lease term.",
        ),
        (
            uuid.uuid4(),
            "assignment_clause",
            "Tenant may not assign this lease without prior written consent of Landlord, which may be withheld in Landlord's sole discretion.",
        ),
    ]
    analyzer = LeaseClauseAnalyzer()
    result = await analyzer.analyze(transcript, clauses, documents=[])

    assert result["mode"] == "deterministic"
    # Both topics matched at least once.
    matched_topics = {m["topic"] for m in result["matches"]}
    assert "renewal" in matched_topics
    assert "assignment" in matched_topics

    # Conflict on renewal window (30 vs 90 days).
    duration_conflicts = [c for c in result["conflicts"] if c["conflict_type"] == "duration_window"]
    assert duration_conflicts, result["conflicts"]
    assert set(duration_conflicts[0]["values"]) >= {30, 90}

    # Talking points include a flag for the conflicting renewal terms.
    points_text = " ".join(p["point"].lower() for p in result["talking_points"])
    assert "conflicting" in points_text


@pytest.mark.asyncio
async def test_ambiguity_detection():
    from app.services.lease_clause_analyzer import LeaseClauseAnalyzer
    transcript = "What is the rent escalation clause for next year?"
    # Escalation clause that fails to specify a percentage — should be flagged ambiguous.
    clauses = [
        (
            uuid.uuid4(),
            "rent_escalation",
            "Rent shall escalate annually per the prevailing market conditions and CPI adjustments as determined by Landlord.",
        ),
    ]
    analyzer = LeaseClauseAnalyzer()
    result = await analyzer.analyze(transcript, clauses, documents=[])
    amb = result["ambiguities"]
    assert any("rent escalation percentage" in (issue or "")
               for a in amb for issue in a.get("issues", [])), amb


@pytest.mark.asyncio
async def test_empty_transcript_returns_no_transcript():
    from app.services.lease_clause_analyzer import LeaseClauseAnalyzer
    analyzer = LeaseClauseAnalyzer()
    result = await analyzer.analyze("", [], [])
    assert result["mode"] == "no_transcript"
    assert result["matches"] == []


async def _seed_lease_with_clauses_and_voice(
    auth_client, db_session, transcript: str | None = None,
):
    from app.models.lease import CommercialLease
    from app.models.lease_clause import LeaseClause
    from app.models.clause_query import ClauseQuery
    from app.models.user import User
    from sqlalchemy import select

    # Identify current user.
    me_resp = await auth_client.get("/api/v1/auth/me")
    assert me_resp.status_code == 200, me_resp.text
    user_id = uuid.UUID(me_resp.json()["id"])

    # Create the lease.
    lease = CommercialLease(
        property_address=f"100 Main St #{uuid.uuid4().hex[:4]}",
        tenant_name="Phase B Test Tenant",
        landlord_name="Phase B Landlord",
        lease_type="gross",
        term_start=date(2024, 1, 1),
        term_end=date(2029, 12, 31),
        base_rent=5500.0,
        rent_escalation_pct=3.0,
        status="active",
        suite_number="200",
        square_footage=4000.0,
        created_by=user_id,
    )
    db_session.add(lease)
    await db_session.commit()
    await db_session.refresh(lease)

    # Two clauses on renewal — different notice windows (will trigger conflict).
    c1 = LeaseClause(
        lease_id=lease.id,
        clause_type="renewal_option",
        extracted_text="Tenant may exercise the renewal option by providing 30 days written notice.",
        risk_score=40,
    )
    c2 = LeaseClause(
        lease_id=lease.id,
        clause_type="renewal_option",
        extracted_text="Tenant must provide 90 days written notice to renew the lease.",
        risk_score=55,
    )
    db_session.add_all([c1, c2])
    await db_session.commit()

    if transcript is not None:
        cq = ClauseQuery(
            lease_id=lease.id,
            author_id=user_id,
            voice_file_url="blob://test/audio.mp3",
            voice_transcript=transcript,
            transcript_status="completed",
            provider="deepinfra",
            model="openai/whisper-large-v3",
            routed_to_counsel="true",
            status="awaiting_counsel",
        )
        db_session.add(cq)
        await db_session.commit()

    return lease.id


@pytest.mark.asyncio
async def test_cross_validate_voice_endpoint(auth_client, db_session):
    transcript = (
        "We need to renew the lease but I'm confused about the notice window. "
        "Section 5 says 30 days but section 11 says 90 days — which one wins?"
    )
    lease_id = await _seed_lease_with_clauses_and_voice(
        auth_client, db_session, transcript=transcript,
    )
    res = await auth_client.post(f"/api/v1/leases/{lease_id}/cross-validate-voice")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "completed"
    assert body["mode"] == "deterministic"
    assert body["clauses_checked"] == 2
    assert "renewal" in body["topics"]
    duration_conflicts = [c for c in body["conflicts"] if c["conflict_type"] == "duration_window"]
    assert duration_conflicts
    assert body["talking_points"]


@pytest.mark.asyncio
async def test_cross_validate_no_transcript(auth_client, db_session):
    lease_id = await _seed_lease_with_clauses_and_voice(auth_client, db_session, transcript=None)
    res = await auth_client.post(f"/api/v1/leases/{lease_id}/cross-validate-voice")
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "no_transcript"


@pytest.mark.asyncio
async def test_tenant_briefing_pdf_renders(auth_client, db_session):
    transcript = (
        "Can we sublet the second floor to a software company next year? "
        "Also — what's the renewal notice window?"
    )
    lease_id = await _seed_lease_with_clauses_and_voice(
        auth_client, db_session, transcript=transcript,
    )
    pdf = await auth_client.get(f"/api/v1/leases/{lease_id}/tenant-briefing.pdf")
    assert pdf.status_code == 200, pdf.text
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert pdf.content[:4] == b"%PDF"
    assert "leaseiq-tenant-briefing-" in pdf.headers.get("content-disposition", "")
    assert pdf.headers.get("x-leaseiq-mode") == "deterministic"


@pytest.mark.asyncio
async def test_cross_validate_unknown_lease_404(auth_client):
    res = await auth_client.post(
        "/api/v1/leases/00000000-0000-0000-0000-000000000000/cross-validate-voice"
    )
    assert res.status_code == 404
