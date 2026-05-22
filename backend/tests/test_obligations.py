from __future__ import annotations
import pytest
from datetime import date, timedelta


@pytest.mark.asyncio
async def test_create_obligation(auth_client, sample_lease):
    """Test creating an obligation."""
    obligation_data = {
        "lease_id": str(sample_lease.id),
        "obligation_type": "rent_payment",
        "due_date": "2024-03-01",
        "recurrence": "monthly",
        "amount": 5000.00,
        "responsible_party": "Tenant",
    }

    response = await auth_client.post("/api/v1/obligations", json=obligation_data)

    assert response.status_code == 201
    data = response.json()
    assert data["obligation_type"] == "rent_payment"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_obligations_by_lease(auth_client, sample_lease, db_session):
    """Test listing obligations for a lease."""
    from app.models.obligation import Obligation

    oblig = Obligation(
        lease_id=sample_lease.id,
        obligation_type="insurance",
        due_date=date.today() + timedelta(days=30),
        status="pending",
    )
    db_session.add(oblig)
    await db_session.commit()

    response = await auth_client.get(f"/api/v1/obligations/lease/{sample_lease.id}")

    assert response.status_code == 200
    obligations = response.json()
    assert len(obligations) >= 1


@pytest.mark.asyncio
async def test_get_overdue_obligations(auth_client, sample_lease, db_session):
    """Test retrieving overdue obligations."""
    from app.models.obligation import Obligation

    overdue_oblig = Obligation(
        lease_id=sample_lease.id,
        obligation_type="maintenance",
        due_date=date.today() - timedelta(days=5),
        status="pending",
    )
    db_session.add(overdue_oblig)
    await db_session.commit()

    response = await auth_client.get("/api/v1/obligations/overdue")

    assert response.status_code == 200
    overdue = response.json()
    assert any(o["obligation_type"] == "maintenance" for o in overdue)


@pytest.mark.asyncio
async def test_get_upcoming_obligations(auth_client, sample_lease, db_session):
    """Test retrieving upcoming obligations."""
    from app.models.obligation import Obligation

    upcoming_oblig = Obligation(
        lease_id=sample_lease.id,
        obligation_type="inspection",
        due_date=date.today() + timedelta(days=15),
        status="pending",
    )
    db_session.add(upcoming_oblig)
    await db_session.commit()

    response = await auth_client.get("/api/v1/obligations/upcoming?days=30")

    assert response.status_code == 200
    upcoming = response.json()
    assert any(o["obligation_type"] == "inspection" for o in upcoming)


@pytest.mark.asyncio
async def test_mark_obligation_complete(auth_client, sample_lease, db_session):
    """Test marking an obligation as completed."""
    from app.models.obligation import Obligation

    oblig = Obligation(
        lease_id=sample_lease.id,
        obligation_type="report",
        due_date=date.today() + timedelta(days=10),
        status="pending",
    )
    db_session.add(oblig)
    await db_session.commit()
    await db_session.refresh(oblig)

    response = await auth_client.post(f"/api/v1/obligations/{oblig.id}/complete")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_update_obligation(auth_client, sample_lease, db_session):
    """Test updating an obligation."""
    from app.models.obligation import Obligation

    oblig = Obligation(
        lease_id=sample_lease.id,
        obligation_type="payment",
        due_date=date.today() + timedelta(days=10),
        status="pending",
    )
    db_session.add(oblig)
    await db_session.commit()
    await db_session.refresh(oblig)

    update_data = {"status": "overdue"}
    response = await auth_client.patch(f"/api/v1/obligations/{oblig.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "overdue"
