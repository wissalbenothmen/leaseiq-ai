from __future__ import annotations
import uuid
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict, model_validator


class CommercialLeaseCreate(BaseModel):
    property_address: str
    tenant_name: str
    landlord_name: str
    lease_type: str = "gross"
    term_start: date
    term_end: date
    base_rent: Optional[float] = None
    rent_escalation_pct: Optional[float] = None
    suite_number: Optional[str] = None
    square_footage: Optional[float] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_term_dates(self) -> "CommercialLeaseCreate":
        if self.term_end <= self.term_start:
            raise ValueError("term_end must be after term_start")
        return self


class CommercialLeaseUpdate(BaseModel):
    property_address: Optional[str] = None
    tenant_name: Optional[str] = None
    landlord_name: Optional[str] = None
    lease_type: Optional[str] = None
    term_start: Optional[date] = None
    term_end: Optional[date] = None
    base_rent: Optional[float] = None
    rent_escalation_pct: Optional[float] = None
    status: Optional[str] = None
    suite_number: Optional[str] = None
    square_footage: Optional[float] = None
    notes: Optional[str] = None


class CommercialLeaseResponse(BaseModel):
    id: uuid.UUID
    property_address: str
    tenant_name: str
    landlord_name: str
    lease_type: str
    term_start: date
    term_end: date
    base_rent: Optional[float]
    rent_escalation_pct: Optional[float]
    status: str
    suite_number: Optional[str]
    square_footage: Optional[float]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommercialLeaseListResponse(BaseModel):
    id: uuid.UUID
    property_address: str
    tenant_name: str
    landlord_name: str
    lease_type: str
    term_start: date
    term_end: date
    base_rent: Optional[float]
    status: str
    square_footage: Optional[float]

    model_config = ConfigDict(from_attributes=True)
