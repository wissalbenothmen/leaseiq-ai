from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict


class LeaseClauseCreate(BaseModel):
    lease_id: uuid.UUID
    clause_type: str
    extracted_text: str
    risk_score: int = 0
    risk_factors: Optional[list[Any]] = None
    landlord_favorable: Optional[str] = "false"
    tenant_favorable: Optional[str] = "false"
    confidence_score: Optional[float] = None
    extraction_json: Optional[dict] = None


class LeaseClauseUpdate(BaseModel):
    risk_score: Optional[int] = None
    landlord_favorable: Optional[str] = None
    tenant_favorable: Optional[str] = None


class LeaseClauseResponse(BaseModel):
    id: uuid.UUID
    lease_id: uuid.UUID
    clause_type: str
    extracted_text: str
    risk_score: int
    risk_factors: Optional[list[Any]]
    landlord_favorable: str
    tenant_favorable: str
    confidence_score: Optional[float]
    ai_summary: Optional[str] = None
    ai_recommendations: Optional[list[Any]] = None
    ai_analyzed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeaseClauseListResponse(BaseModel):
    id: uuid.UUID
    clause_type: str
    extracted_text: str
    risk_score: int
    risk_factors: Optional[list[Any]]
    landlord_favorable: str
    tenant_favorable: str
    confidence_score: Optional[float]
    ai_summary: Optional[str] = None
    ai_recommendations: Optional[list[Any]] = None
    ai_analyzed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
