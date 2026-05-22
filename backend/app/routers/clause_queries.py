"""Voice clause-query router — Phase A from the audit-pipeline recipe.

POST /api/v1/clause-queries/lease/{lease_id}/upload  — audio → Whisper → ClauseQuery
GET  /api/v1/clause-queries/lease/{lease_id}         — list verbal questions
"""
from __future__ import annotations

import os
import tempfile
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.auth import get_current_user
from app.database import get_db
from app.services.whisper_service import WhisperService

router = APIRouter(prefix="/clause-queries", tags=["clause-queries"])

_ALLOWED_AUDIO_EXT = {".wav", ".mp3", ".m4a", ".mp4", ".webm", ".ogg", ".flac"}


def _validate_audio_filename(filename: str) -> str:
    if not filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    ext = os.path.splitext(filename)[1].lower()
    if ext not in _ALLOWED_AUDIO_EXT:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported audio type {ext!r}. Allowed: {sorted(_ALLOWED_AUDIO_EXT)}",
        )
    return ext


def _serialize(q: models.ClauseQuery) -> Dict[str, Any]:
    return {
        "id": str(q.id),
        "lease_id": str(q.lease_id),
        "clause_id": str(q.clause_id) if q.clause_id else None,
        "voice_file_url": q.voice_file_url,
        "voice_transcript": q.voice_transcript,
        "transcript_status": q.transcript_status,
        "provider": q.provider,
        "model": q.model,
        "routed_to_counsel": q.routed_to_counsel == "true",
        "counsel_response": q.counsel_response,
        "status": q.status,
        "created_at": q.created_at.isoformat() if q.created_at else None,
    }


@router.post("/lease/{lease_id}/upload", status_code=status.HTTP_201_CREATED)
async def upload_clause_query(
    lease_id: uuid.UUID,
    file: UploadFile = File(...),
    clause_id: Optional[uuid.UUID] = Form(None),
    routed_to_counsel: bool = Form(True),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Upload an asset-manager verbal question → Whisper transcript → ClauseQuery row."""
    lease_q = await db.execute(
        select(models.CommercialLease).where(models.CommercialLease.id == lease_id)
    )
    if not lease_q.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lease not found")

    ext = _validate_audio_filename(file.filename or "")
    content_bytes = await file.read()
    if not content_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(content_bytes)
        tmp_path = tmp.name

    try:
        whisper = WhisperService()
        result = await whisper.transcribe_audio(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    transcript = result.get("transcript", "") or ""

    query = models.ClauseQuery(
        lease_id=lease_id,
        clause_id=clause_id,
        author_id=current_user.id,
        voice_file_url=f"blob://clause-queries/{file.filename}",
        voice_transcript=transcript,
        transcript_status="completed" if transcript else "failed",
        provider=result.get("provider"),
        model=result.get("model"),
        routed_to_counsel="true" if routed_to_counsel else "false",
        status="awaiting_counsel" if routed_to_counsel else "draft",
    )
    db.add(query)
    await db.commit()
    await db.refresh(query)
    return _serialize(query)


@router.get("/lease/{lease_id}")
async def list_clause_queries(
    lease_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    lease_q = await db.execute(
        select(models.CommercialLease).where(models.CommercialLease.id == lease_id)
    )
    if not lease_q.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lease not found")

    q = await db.execute(
        select(models.ClauseQuery)
        .where(models.ClauseQuery.lease_id == lease_id)
        .order_by(models.ClauseQuery.created_at.desc())
    )
    return [_serialize(row) for row in q.scalars().all()]
