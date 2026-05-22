from __future__ import annotations
import pytest
from datetime import date, timedelta


@pytest.mark.asyncio
async def test_portfolio_risk_summary(auth_client, sample_lease, db_session):
    """Test portfolio risk summary returns aggregated clause data."""
    from app.models.lease_clause import LeaseClause

    clause = LeaseClause(
        lease_id=sample_lease.id,
        clause_type="personal_guarantee",
        extracted_text="Tenant guarantees all obligations.",
        risk_score=90,
    )
    db_session.add(clause)
    await db_session.commit()

    response = await auth_client.get("/api/v1/analytics/portfolio/risk-summary")

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert isinstance(data["summary"], list)
    assert any(item["clause_type"] == "personal_guarantee" for item in data["summary"])


@pytest.mark.asyncio
async def test_expiring_leases(auth_client, sample_lease):
    """Test expiring leases endpoint returns leases within window."""
    response = await auth_client.get("/api/v1/analytics/portfolio/expiring-leases?days=3650")

    assert response.status_code == 200
    data = response.json()
    assert "expiring_count" in data
    assert "leases" in data
    assert isinstance(data["leases"], list)


@pytest.mark.asyncio
async def test_obligation_compliance(auth_client, sample_lease, db_session):
    """Test obligation compliance endpoint returns compliance rate."""
    from app.models.obligation import Obligation

    oblig = Obligation(
        lease_id=sample_lease.id,
        obligation_type="rent_payment",
        due_date=date.today() + timedelta(days=5),
        status="pending",
    )
    db_session.add(oblig)
    await db_session.commit()

    response = await auth_client.get("/api/v1/analytics/portfolio/obligation-compliance")

    assert response.status_code == 200
    data = response.json()
    assert "compliance_rate" in data
    assert "total_obligations" in data
    assert 0.0 <= data["compliance_rate"] <= 100.0


@pytest.mark.asyncio
async def test_lease_risk_breakdown(auth_client, sample_lease, db_session):
    """Test per-lease risk breakdown respects configured thresholds."""
    from app.models.lease_clause import LeaseClause

    high = LeaseClause(
        lease_id=sample_lease.id,
        clause_type="cam_charges",
        extracted_text="Uncapped CAM charges.",
        risk_score=80,
    )
    medium = LeaseClause(
        lease_id=sample_lease.id,
        clause_type="subletting",
        extracted_text="Subletting requires consent.",
        risk_score=55,
    )
    low = LeaseClause(
        lease_id=sample_lease.id,
        clause_type="renewal_option",
        extracted_text="Fair market renewal.",
        risk_score=15,
    )
    db_session.add_all([high, medium, low])
    await db_session.commit()

    response = await auth_client.get(f"/api/v1/analytics/lease/{sample_lease.id}/risk-breakdown")

    assert response.status_code == 200
    data = response.json()
    assert data["high_risk_count"] >= 1
    assert data["medium_risk_count"] >= 1
    assert data["low_risk_count"] >= 1


@pytest.mark.asyncio
async def test_lease_status_distribution(auth_client, sample_lease):
    """Test lease status distribution endpoint."""
    response = await auth_client.get("/api/v1/analytics/portfolio/lease-status-distribution")

    assert response.status_code == 200
    data = response.json()
    assert "distribution" in data
    assert isinstance(data["distribution"], list)
    assert any(item["status"] == "active" for item in data["distribution"])


@pytest.mark.asyncio
async def test_lease_risk_breakdown_no_clauses(auth_client, sample_lease):
    """Test risk breakdown for a lease with no clauses returns zero counts."""
    import uuid
    fake_id = "00000000-0000-0000-0000-000000000099"
    response = await auth_client.get(f"/api/v1/analytics/lease/{fake_id}/risk-breakdown")

    assert response.status_code == 200
    data = response.json()
    assert data["total_clauses"] == 0
    assert data["avg_risk"] == 0
