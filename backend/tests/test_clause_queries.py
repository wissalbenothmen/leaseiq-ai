"""Phase A — verbal clause-query transcription tests for LeaseIQ."""
from __future__ import annotations

import pytest


async def _make_lease(auth_client) -> str:
    """Create a lease via API and return its id (string)."""
    res = await auth_client.post(
        "/api/v1/leases",
        json={
            "property_address": "1 Voice Test Plaza, NYC",
            "tenant_name": "Voice Tenant Inc",
            "landlord_name": "Voice Landlord LLC",
            "lease_type": "gross",
            "term_start": "2024-01-01",
            "term_end": "2029-12-31",
            "base_rent": 10000.0,
            "suite_number": "VC1",
            "square_footage": 5000.0,
        },
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


@pytest.mark.asyncio
async def test_clause_query_lifecycle(auth_client):
    """Upload verbal question → mock Whisper transcribes → ClauseQuery persisted."""
    lease_id = await _make_lease(auth_client)

    files = {"file": ("query.wav", b"\x00fake_audio_bytes", "audio/wav")}
    data = {"routed_to_counsel": "true"}
    up = await auth_client.post(
        f"/api/v1/clause-queries/lease/{lease_id}/upload",
        files=files,
        data=data,
    )
    assert up.status_code == 201, up.text
    body = up.json()
    assert body["lease_id"] == lease_id
    assert body["transcript_status"] == "completed"
    assert body["voice_transcript"], "transcript should be populated"
    # Mock canned transcript mentions Section 14.3 / counsel
    assert "Section 14.3" in body["voice_transcript"] or "counsel" in body["voice_transcript"]
    assert body["routed_to_counsel"] is True
    assert body["status"] == "awaiting_counsel"

    # List endpoint returns the persisted query
    listed = await auth_client.get(f"/api/v1/clause-queries/lease/{lease_id}")
    assert listed.status_code == 200
    items = listed.json()
    assert len(items) == 1
    assert items[0]["id"] == body["id"]


@pytest.mark.asyncio
async def test_clause_query_rejects_bad_extension(auth_client):
    lease_id = await _make_lease(auth_client)
    res = await auth_client.post(
        f"/api/v1/clause-queries/lease/{lease_id}/upload",
        files={"file": ("note.txt", b"hi", "text/plain")},
    )
    assert res.status_code == 415


@pytest.mark.asyncio
async def test_clause_query_unknown_lease_404(auth_client):
    res = await auth_client.get(
        "/api/v1/clause-queries/lease/00000000-0000-0000-0000-000000000000"
    )
    assert res.status_code == 404
