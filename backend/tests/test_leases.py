from __future__ import annotations
import pytest
from datetime import date


@pytest.mark.asyncio
async def test_create_lease(auth_client):
    """Test creating a new lease."""
    lease_data = {
        "property_address": "456 Oak Ave, Boston, MA",
        "tenant_name": "Tech Startup Inc",
        "landlord_name": "Boston Properties",
        "lease_type": "net",
        "term_start": "2023-01-01",
        "term_end": "2028-12-31",
        "base_rent": 7500.00,
        "rent_escalation_pct": 2.5,
        "suite_number": "200",
        "square_footage": 8000.0,
    }

    response = await auth_client.post("/api/v1/leases", json=lease_data)

    assert response.status_code == 201
    data = response.json()
    assert data["tenant_name"] == "Tech Startup Inc"
    assert data["status"] == "active"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_leases(auth_client, sample_lease):
    """Test listing leases."""
    response = await auth_client.get("/api/v1/leases")

    assert response.status_code == 200
    leases = response.json()
    assert isinstance(leases, list)
    assert len(leases) >= 1


@pytest.mark.asyncio
async def test_list_leases_filter_by_status(auth_client, sample_lease):
    """Test filtering leases by status."""
    response = await auth_client.get("/api/v1/leases?status=active")

    assert response.status_code == 200
    leases = response.json()
    assert all(lease["status"] == "active" for lease in leases)


@pytest.mark.asyncio
async def test_list_leases_filter_by_tenant(auth_client, sample_lease):
    """Test filtering leases by tenant name."""
    response = await auth_client.get("/api/v1/leases?tenant_name=Acme")

    assert response.status_code == 200
    leases = response.json()
    assert all("Acme" in lease["tenant_name"] for lease in leases)


@pytest.mark.asyncio
async def test_get_lease(auth_client, sample_lease):
    """Test retrieving a specific lease."""
    response = await auth_client.get(f"/api/v1/leases/{sample_lease.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_lease.id)
    assert data["tenant_name"] == sample_lease.tenant_name


@pytest.mark.asyncio
async def test_update_lease(auth_client, sample_lease):
    """Test updating a lease."""
    update_data = {
        "base_rent": 5500.00,
        "rent_escalation_pct": 4.0,
    }

    response = await auth_client.patch(f"/api/v1/leases/{sample_lease.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["base_rent"] == 5500.00
    assert data["rent_escalation_pct"] == 4.0


@pytest.mark.asyncio
async def test_delete_lease(auth_client, sample_lease):
    """Test deleting a lease."""
    response = await auth_client.delete(f"/api/v1/leases/{sample_lease.id}")

    assert response.status_code == 204

    get_response = await auth_client.get(f"/api/v1/leases/{sample_lease.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_lease(auth_client):
    """Test getting a non-existent lease."""
    response = await auth_client.get("/api/v1/leases/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_lease_invalid_dates(auth_client):
    """Test that term_end before term_start is rejected."""
    lease_data = {
        "property_address": "789 Invalid Dr, NYC, NY",
        "tenant_name": "Bad Date Corp",
        "landlord_name": "Owner LLC",
        "lease_type": "gross",
        "term_start": "2025-06-01",
        "term_end": "2025-01-01",  # before term_start
    }

    response = await auth_client.post("/api/v1/leases", json=lease_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_lease_equal_dates(auth_client):
    """Test that term_end equal to term_start is rejected."""
    lease_data = {
        "property_address": "789 Invalid Dr, NYC, NY",
        "tenant_name": "Same Date Corp",
        "landlord_name": "Owner LLC",
        "lease_type": "gross",
        "term_start": "2025-01-01",
        "term_end": "2025-01-01",  # same as term_start
    }

    response = await auth_client.post("/api/v1/leases", json=lease_data)

    assert response.status_code == 422
