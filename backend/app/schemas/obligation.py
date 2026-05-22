from __future__ import annotations
import uuid
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ObligationCreate(BaseModel):
    lease_id: uuid.UUID
    obligation_type: str
    due_date: date
    recurrence: str = "one_time"
    amount: Optional[float] = None
    description: Optional[str] = None
    responsible_party: Optional[str] = None


class ObligationUpdate(BaseModel):
    status: Optional[str] = None
    due_date: Optional[date] = None
    amount: Optional[float] = None


class ObligationResponse(BaseModel):
    id: uuid.UUID
    lease_id: uuid.UUID
    obligation_type: str
    due_date: date
    recurrence: str
    status: str
    amount: Optional[float]
    description: Optional[str]
    responsible_party: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ObligationListResponse(BaseModel):
    id: uuid.UUID
    obligation_type: str
    due_date: date
    recurrence: str
    status: str
    amount: Optional[float]

    model_config = ConfigDict(from_attributes=True)
