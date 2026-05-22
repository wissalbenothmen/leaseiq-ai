from __future__ import annotations
import uuid
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CriticalDateCreate(BaseModel):
    lease_id: uuid.UUID
    date_type: str
    date_value: date
    days_until: Optional[int] = None


class CriticalDateUpdate(BaseModel):
    alert_sent: Optional[str] = None


class CriticalDateResponse(BaseModel):
    id: uuid.UUID
    lease_id: uuid.UUID
    date_type: str
    date_value: date
    days_until: Optional[int]
    alert_sent: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CriticalDateListResponse(BaseModel):
    id: uuid.UUID
    date_type: str
    date_value: date
    days_until: Optional[int]
    alert_sent: str

    model_config = ConfigDict(from_attributes=True)
