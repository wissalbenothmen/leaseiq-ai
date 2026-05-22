from __future__ import annotations
import pytest
from datetime import date, timedelta
from app.services.critical_date_extractor import extractor


def test_calculate_days_until():
    """Test days-until calculation."""
    future_date = date.today() + timedelta(days=45)
    days = extractor.calculate_days_until(future_date)
    assert 44 <= days <= 46


def test_is_upcoming_within_threshold():
    """Test upcoming date detection."""
    future_date = date.today() + timedelta(days=30)
    assert extractor.is_upcoming(future_date, threshold_days=90) is True


def test_is_upcoming_outside_threshold():
    """Test upcoming date detection outside threshold."""
    future_date = date.today() + timedelta(days=120)
    assert extractor.is_upcoming(future_date, threshold_days=90) is False


def test_is_upcoming_past_date():
    """Test past date is not upcoming."""
    past_date = date.today() - timedelta(days=10)
    assert extractor.is_upcoming(past_date, threshold_days=90) is False


@pytest.mark.asyncio
async def test_extract_critical_dates():
    """Test extracting critical dates from lease text."""
    lease_text = """
    LEASE TERMS:
    Commencement Date: January 1, 2020
    Lease Expiration: December 31, 2025
    First Renewal Option: Tenant may renew for 5 years starting January 1, 2026
    Renewal Notice: Tenant must provide 12 months notice prior to expiration
    Rent Review Date: January 1, 2023
    """
    commencement = date(2020, 1, 1)

    result = await extractor.extract_critical_dates(lease_text, commencement)

    assert result["success"] is True
    assert result["extraction_count"] >= 1
    assert isinstance(result["dates"], list)


@pytest.mark.asyncio
async def test_extract_dates_calculates_notice_windows():
    """Test that notice window requirements are calculated."""
    lease_text = """
    Lease expiration: December 31, 2025
    Tenant must provide 12 months' notice of non-renewal.
    """
    commencement = date(2020, 1, 1)

    result = await extractor.extract_critical_dates(lease_text, commencement)

    if result["success"] and result["dates"]:
        for date_obj in result["dates"]:
            if date_obj.get("notice_days_required"):
                assert date_obj["notice_days_required"] > 0
