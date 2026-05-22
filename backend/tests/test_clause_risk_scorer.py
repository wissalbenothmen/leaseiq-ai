from __future__ import annotations
import pytest
from app.services.clause_risk_scorer import scorer


@pytest.mark.asyncio
async def test_score_personal_guarantee_high_risk():
    """Test that personal guarantee without cap scores as high risk."""
    clause_type = "personal_guarantee"
    clause_text = "Tenant guarantees all lease obligations. No cap on guarantee amount."

    result = await scorer.score_clause(clause_type, clause_text)

    assert result["success"] is True
    assert result["risk_score"] >= 80
    assert len(result["risk_factors"]) > 0


@pytest.mark.asyncio
async def test_score_standard_rent_escalation_medium_risk():
    """Test that standard rent escalation scores as medium risk."""
    clause_type = "rent_escalation"
    clause_text = "Base rent shall increase by 3% annually on anniversary date."

    result = await scorer.score_clause(clause_type, clause_text)

    assert result["success"] is True
    assert 15 <= result["risk_score"] <= 35
    assert "escalation" in " ".join(result["risk_factors"]).lower()


@pytest.mark.asyncio
async def test_score_favorable_renewal_low_risk():
    """Test that favorable renewal terms score as low risk."""
    clause_type = "renewal_option"
    clause_text = "Tenant has 2 renewal options at fair market value to be negotiated."

    result = await scorer.score_clause(clause_type, clause_text)

    assert result["success"] is True
    assert result["risk_score"] <= 30


@pytest.mark.asyncio
async def test_score_uncapped_cam_high_risk():
    """Test that uncapped CAM charges score as high risk."""
    clause_type = "cam_charges"
    clause_text = "Tenant pays pro-rata share of all CAM charges with no cap or exclusions."

    result = await scorer.score_clause(clause_type, clause_text)

    assert result["success"] is True
    assert result["risk_score"] >= 70


@pytest.mark.asyncio
async def test_score_no_subletting_medium_risk():
    """Test that no subletting restrictions score as medium risk."""
    clause_type = "subletting"
    clause_text = "Tenant may not sublet any portion of the space without landlord consent."

    result = await scorer.score_clause(clause_type, clause_text)

    assert result["success"] is True
    assert 50 <= result["risk_score"] <= 80


@pytest.mark.asyncio
async def test_multiple_clauses_parallel():
    """Test scoring multiple clauses in parallel."""
    clauses = [
        {
            "type": "personal_guarantee",
            "text": "Tenant guarantees all obligations without cap.",
        },
        {
            "type": "rent_escalation",
            "text": "Rent increases 3% annually.",
        },
        {
            "type": "renewal_option",
            "text": "Fair market value renewal option.",
        },
    ]

    results = await scorer.score_multiple_clauses(clauses)

    assert len(results) == 3
    assert results[0]["risk_score"] >= 80
    assert 15 <= results[1]["risk_score"] <= 35
    assert results[2]["risk_score"] <= 30
