from __future__ import annotations
import asyncio
import json
import logging
from typing import Optional
from openai import AsyncOpenAI
from app.config import get_settings

settings = get_settings()
_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
logger = logging.getLogger(__name__)


class ClauseRiskScorer:
    """Service to score lease clauses for risk using GPT-4.1 Mini."""

    def _rule_based_score(self, clause_type: str, clause_text: str) -> dict:
        """Fallback rule-based scoring when AI is unavailable."""
        import re
        t = clause_type.lower()
        txt = clause_text.lower()

        def _has_cap_protection() -> bool:
            protected = bool(re.search(r'\bcapped at\b|\bcap of\b|\blimited to\b|\blimited liability\b', txt))
            negated = bool(re.search(r'\bno cap\b|\bwithout cap\b|\buncapped\b|\bno limit\b|\bwithout limit\b', txt))
            return protected and not negated

        score: int
        factors: list[str]
        summary: str
        recommendations: list[str]

        if "personal_guarantee" in t:
            if _has_cap_protection():
                score = 55
                factors = ["personal guarantee present", "liability cap in place"]
                summary = ("Personal guarantee clause with a liability cap. The cap limits your financial "
                           "exposure, but you remain personally liable up to the stated ceiling.")
                recommendations = [
                    "Confirm the cap amount is clearly defined and indexed to a fixed figure",
                    "Request a burn-down provision reducing the guarantee over time as obligations are met",
                    "Negotiate a release clause if the tenant maintains a satisfactory payment record for 24 months",
                ]
            else:
                score = 90
                factors = ["personal guarantee without cap", "unlimited personal liability", "high financial exposure"]
                summary = ("Uncapped personal guarantee clause — the guarantor is personally liable for all lease "
                           "obligations without limit. This is the highest-risk clause type in commercial leases.")
                recommendations = [
                    "Negotiate an absolute cap on the guarantee equal to 12 months of base rent",
                    "Push for a sunset clause expiring the guarantee after 2–3 years of clean payment history",
                    "Seek to replace the personal guarantee with a letter of credit or security deposit",
                    "If the guarantee cannot be removed, ensure the cap is clearly defined in writing",
                ]

        elif "cam_charges" in t or "cam" in t:
            has_cap = _has_cap_protection() or bool(
                re.search(r'\bcap\b|\bexclusion\b', txt) and
                not re.search(r'\bno cap\b|\buncapped\b', txt)
            )
            if has_cap:
                score = 40
                factors = ["CAM charges present", "cap or exclusions in place"]
                summary = ("Common Area Maintenance charges apply with a cap or specific exclusions. "
                           "The protection limits your exposure to CAM escalation.")
                recommendations = [
                    "Confirm the cap applies to controllable expenses only (not taxes, insurance)",
                    "Request an audit right to verify CAM calculations annually",
                    "Ensure capital expenditures are explicitly excluded from CAM reconciliation",
                ]
            else:
                score = 78
                factors = ["uncapped CAM charges", "no exclusions defined", "open-ended operating cost exposure"]
                summary = ("Uncapped CAM charges clause with no defined exclusions. Landlord can pass through "
                           "any operating cost increase without limit, creating significant financial exposure.")
                recommendations = [
                    "Negotiate a hard annual CAM increase cap of 3–5% on controllable expenses",
                    "Exclude capital expenditures, management fees above 3%, and landlord's overhead from CAM",
                    "Request the right to audit CAM statements within 12 months of each reconciliation",
                    "Push for a gross-up provision that normalizes CAM calculations at 95% occupancy",
                ]

        elif "subletting" in t or "sublet" in t or "assignment" in t:
            restricted = bool(re.search(
                r'may not sublet|not sublet|without\s+(?:landlord\s+)?consent|no subletting|50%|profit', txt
            ))
            has_profit_share = bool(re.search(r'\d+%.*profit|profit.*\d+%', txt))
            if restricted or has_profit_share:
                score = 65
                factors = ["landlord consent required", "subletting restricted", "profit sharing obligation"]
                summary = ("Subletting requires landlord consent and includes a profit-sharing clause. "
                           "The 50% profit share materially reduces the economic value of any sublease.")
                recommendations = [
                    "Negotiate to eliminate or reduce the profit-sharing requirement (25% is more standard)",
                    "Define 'not unreasonably withheld' with a 30-day deemed approval timeline",
                    "Carve out corporate affiliates and restructuring-related assignments from consent requirements",
                    "Request a provision allowing subletting to creditworthy tenants without consent if landlord is unresponsive",
                ]
            else:
                score = 45
                factors = ["subletting requires consent", "standard assignment terms"]
                summary = ("Subletting permitted with landlord consent on standard terms. "
                           "The consent requirement is typical but the response timeline should be defined.")
                recommendations = [
                    "Ensure 'consent not unreasonably withheld' is explicitly stated",
                    "Add a 30-day response deadline with deemed approval if landlord fails to respond",
                    "Carve out affiliated company transfers from consent requirements",
                ]

        elif "rent_escalation" in t or "escalation" in t:
            has_cpi = bool(re.search(r'\bcpi\b|consumer price', txt))
            high_fixed = bool(re.search(r'\b[5-9]\s*%|\b10\s*%|compounded', txt))
            if has_cpi and high_fixed:
                score = 55
                factors = ["CPI-linked escalation", "compounded annual increases", "variable rate exposure"]
                summary = ("Rent escalation with both a fixed annual increase and CPI adjustment, compounded. "
                           "The combination of 4% fixed plus uncapped CPI creates meaningful upside rent exposure.")
                recommendations = [
                    "Negotiate a hard cap on total annual increases (e.g., greater of CPI or 4%, max 6%)",
                    "Ensure the CPI index is clearly specified (which measure, which base year)",
                    "Request a floor below which rent cannot decrease even if CPI is negative",
                    "Push for a blended formula: lower of fixed rate or CPI, not the higher of the two",
                ]
            elif has_cpi:
                score = 35
                factors = ["CPI-linked escalation", "variable escalation rate"]
                summary = ("Rent escalation tied to CPI is standard market practice. "
                           "The variability introduces some uncertainty but is generally tenant-favorable compared to fixed high escalations.")
                recommendations = [
                    "Confirm which CPI index applies and request it be locked at lease signing",
                    "Request a cap on annual increases (e.g., CPI but not to exceed 4% per year)",
                    "Ensure the escalation base is the initial rent, not a prior-year figure that could compound adversely",
                ]
            else:
                score = 25
                factors = ["fixed annual rent escalation", "predictable cost structure"]
                summary = ("Fixed annual rent escalation provides full cost predictability. "
                           "This is the most tenant-favorable escalation structure.")
                recommendations = [
                    "Confirm the escalation is simple (not compounded) unless the rate is below 2%",
                    "Document the exact anniversary date from which escalation applies",
                ]

        elif "renewal_option" in t or "renewal" in t:
            if re.search(r'fair market|negotiate|negotiated', txt):
                score = 15
                factors = ["renewal option at market rate", "negotiated renewal terms"]
                summary = ("Renewal option at fair market rent is the standard best-practice structure. "
                           "It provides tenure protection while ensuring market-aligned economics.")
                recommendations = [
                    "Define the process for determining fair market rent (appraisal, broker survey, or negotiation)",
                    "Include a floor that renewal rent cannot exceed the expiring rent by more than X%",
                    "Ensure the option notice period (typically 6–12 months before expiry) is clearly stated",
                ]
            else:
                score = 20
                factors = ["renewal option present", "fixed renewal terms"]
                summary = ("Renewal option present with defined terms, giving the tenant a right to extend. "
                           "This is a tenant-favorable clause providing business continuity.")
                recommendations = [
                    "Confirm the notice period for exercising the option is clearly defined",
                    "Ensure the renewal option survives early lease assignment",
                    "Request the right to renew for multiple successive terms",
                ]

        elif "termination" in t:
            has_penalty = bool(re.search(r'penalty|fee|unamortized|months?\s+rent', txt))
            long_notice = bool(re.search(r'12\s*month|one\s*year|24\s*month|two\s*year', txt))
            if has_penalty and long_notice:
                score = 65
                factors = ["12-month notice requirement", "termination penalty", "unamortized TI liability"]
                summary = ("Early termination clause with a 12-month notice requirement plus a financial penalty "
                           "equal to 6 months rent plus unamortized tenant improvement allowance. "
                           "The combined notice + penalty creates substantial exit barriers.")
                recommendations = [
                    "Negotiate notice period down to 6 months (industry standard)",
                    "Cap the termination penalty at 3 months rent rather than 6",
                    "Request a penalty step-down: 100% in years 1–2, 75% in years 3–4, 50% thereafter",
                    "Negotiate a landlord mitigation obligation — if replacement tenant is found, penalty reduces proportionally",
                    "Ensure the unamortized TI calculation uses a straight-line method, not accelerated",
                ]
            elif has_penalty:
                score = 50
                factors = ["termination penalty applies", "financial exit barrier"]
                summary = ("Termination clause includes a financial penalty. "
                           "This is standard but the penalty amount and calculation method should be carefully reviewed.")
                recommendations = [
                    "Request a clear formula for calculating the penalty (avoid open-ended language)",
                    "Negotiate a step-down in the penalty amount over time",
                    "Ensure the penalty is the sole and exclusive remedy upon proper notice",
                ]
            else:
                score = 30
                factors = ["termination with notice", "no significant financial penalty"]
                summary = ("Termination with notice but without significant financial penalty. "
                           "This is a relatively tenant-favorable termination structure.")
                recommendations = [
                    "Confirm the notice requirement is in writing and certified mail is acceptable",
                    "Ensure the termination right is mutual (both landlord and tenant)",
                ]

        elif "maintenance" in t:
            tenant_hvac = bool(re.search(r'hvac|heating|cooling|tenant.*responsible|quarterly', txt))
            capital = bool(re.search(r'capital|improvement|approval', txt))
            if tenant_hvac and capital:
                score = 55
                factors = ["tenant responsible for HVAC", "quarterly maintenance required", "capital improvement approval needed"]
                summary = ("Maintenance clause places HVAC servicing obligation on the tenant at quarterly intervals, "
                           "plus requires landlord approval for all capital improvements. "
                           "This is a significant maintenance burden for the tenant.")
                recommendations = [
                    "Request a landlord HVAC maintenance allowance to offset quarterly servicing costs",
                    "Define 'capital improvement' with a clear dollar threshold (e.g., work exceeding $5,000)",
                    "Negotiate a deemed-approval timeline: if landlord does not respond within 15 business days, improvement is approved",
                    "Exclude routine maintenance and emergency repairs from the approval requirement",
                    "Request the right to use approved vendors without landlord pre-authorization each time",
                ]
            else:
                score = 40
                factors = ["tenant maintenance obligations", "standard repair responsibilities"]
                summary = ("Standard maintenance clause assigning interior repair obligations to the tenant. "
                           "Landlord retains structural and common area responsibilities.")
                recommendations = [
                    "Confirm the landlord is responsible for structural components, roof, and building systems",
                    "Define 'reasonable wear and tear' explicitly to avoid end-of-lease disputes",
                    "Include a landlord obligation to maintain common areas to a defined standard",
                ]

        elif "insurance" in t:
            high_limit = bool(re.search(r'\$[5-9],000,000|\$10,000,000|5 million|10 million', txt))
            immediate_default = bool(re.search(r'immediate default|automatic default', txt))
            if immediate_default:
                score = 72
                factors = ["automatic default for insurance lapse", "high liability requirements", "strict compliance obligation"]
                summary = ("Insurance clause with automatic default provision upon coverage lapse. "
                           "Combined with high liability limits, any insurance gap — even briefly — triggers an immediate default.")
                recommendations = [
                    "Remove or soften the 'immediate default' language to allow a 10-day cure period",
                    "Confirm the $5M liability limit is achievable under standard commercial umbrella policies",
                    "Request that the landlord provide 30-day advance notice before declaring default for insurance issues",
                    "Ensure the additional insured designation applies only on a primary and non-contributory basis",
                    "Request waiver of subrogation from both parties to prevent insurer cross-claims",
                ]
            else:
                score = 35
                factors = ["commercial liability insurance required", "additional insured required"]
                summary = ("Standard commercial insurance requirements with reasonable liability limits. "
                           "Additional insured designation is typical and manageable with standard policies.")
                recommendations = [
                    "Verify current policy meets the required limits before signing",
                    "Ensure additional insured coverage is included in your umbrella policy",
                    "Confirm the evidence of insurance (certificate) delivery timeline and maintain a calendar reminder",
                ]

        elif "environmental" in t:
            full_liability = bool(re.search(r'full liability|assume.*all|regardless of cause|indemnif', txt))
            if full_liability:
                score = 82
                factors = ["full environmental liability assumed by tenant", "indemnification regardless of cause", "high contamination exposure"]
                summary = ("Environmental clause requiring the tenant to assume full liability for contamination "
                           "regardless of whether the tenant caused it. This is an extreme risk position with "
                           "potentially unlimited financial exposure.")
                recommendations = [
                    "Negotiate liability limited to contamination actually caused by the tenant during the lease term",
                    "Commission a Phase I Environmental Site Assessment before signing to document baseline conditions",
                    "Request a Phase II assessment if the Phase I reveals recognized environmental conditions (RECs)",
                    "Ensure the indemnification is mutual: landlord indemnifies tenant for pre-existing contamination",
                    "Request a cap on environmental liability tied to the lease value or insurance limits",
                    "Include a provision for government-ordered cleanup using the least-costly acceptable remediation method",
                ]
            else:
                score = 45
                factors = ["environmental obligations present", "standard compliance requirements"]
                summary = ("Environmental clause with standard compliance requirements. "
                           "The scope of tenant liability should be reviewed to confirm it is limited to tenant-caused conditions.")
                recommendations = [
                    "Ensure liability is explicitly limited to contamination caused during the tenant's occupancy",
                    "Request a baseline environmental survey to document pre-existing conditions",
                    "Confirm reporting obligations are limited to incidents caused by the tenant",
                ]

        elif "operating_hours" in t or "hours" in t:
            penalty = bool(re.search(r'penalty|\$\d+|fine', txt))
            mandatory_holidays = bool(re.search(r'holiday|public holiday|all.*holiday', txt))
            if penalty and mandatory_holidays:
                score = 68
                factors = ["mandatory holiday operating requirement", "daily non-compliance penalty", "60-hour minimum week requirement"]
                summary = ("Operating hours clause requiring 60+ hours per week including all major holidays, "
                           "with a daily financial penalty for non-compliance. "
                           "The holiday requirement and penalty structure is highly restrictive.")
                recommendations = [
                    "Negotiate holiday trading to 'best efforts' rather than a mandatory obligation",
                    "Request a force majeure carve-out for health emergencies, staffing shortages, and supply disruptions",
                    "Cap the daily penalty and request a cure period before penalties accrue",
                    "Negotiate a maximum annual penalty cap (e.g., 30 days × daily rate)",
                    "Ensure reduced-hour notice (weather, emergency) is permitted without penalty",
                ]
            else:
                score = 40
                factors = ["operating hour requirements", "standard trading obligations"]
                summary = ("Operating hours clause with standard business hour requirements. "
                           "The obligations are typical for retail leases but should be reviewed for flexibility.")
                recommendations = [
                    "Confirm the minimum hours are achievable with current staffing plans",
                    "Request a force majeure provision covering unavoidable closures",
                    "Ensure reduced hours during initial fit-out period are permitted",
                ]

        else:
            score = 50
            factors = ["clause requires professional review", "non-standard terms present"]
            summary = (f"This {clause_type.replace('_', ' ')} clause contains terms that warrant professional legal review. "
                       "The risk score of 50 reflects moderate uncertainty pending detailed analysis.")
            recommendations = [
                "Engage a commercial real estate attorney to review this clause in full",
                "Compare the clause terms against current market standards for this property type",
                "Ensure any obligations are clearly defined with measurable compliance criteria",
                "Request a cure period for any alleged breach before remedies become available",
            ]

        return {
            "success": True,
            "risk_score": score,
            "risk_factors": factors,
            "landlord_favorable": score >= 60,
            "tenant_favorable": score <= 25,
            "summary": summary,
            "recommendations": recommendations,
        }

    RISK_SCORING_PROMPT_TEMPLATE = """
    Analyze the following lease clause and provide a risk assessment.
    Clause Type: {clause_type}
    Clause Text: {clause_text}

    Return a JSON object with:
    - risk_score: integer (0-100, where 100 is highest risk)
    - risk_factors: array of strings describing risk factors
    - landlord_favorable: boolean (true if heavily landlord-favorable)
    - tenant_favorable: boolean (true if heavily tenant-favorable)
    - summary: brief summary of the clause
    - recommendations: array of recommendations

    RISK GUIDELINES:
    - Personal guarantee (no cap): 85-100
    - Uncapped CAM charges: 75-85
    - No subletting rights: 60-75
    - Force majeure missing: 40-50
    - Standard rent escalation: 20-30
    - Market rate renewal: 10-20
    - Favorable renewal options: 5-15

    Return ONLY valid JSON, no additional text.
    """

    async def score_clause(self, clause_type: str, clause_text: str) -> dict:
        """Score a single clause for risk.

        Uses JSON mode, request timeout, and bounded retry-with-backoff on
        transient errors. Falls back to deterministic rule-based scoring on
        terminal failure.
        """
        prompt = self.RISK_SCORING_PROMPT_TEMPLATE.format(
            clause_type=clause_type, clause_text=clause_text[:4000]
        )

        last_err: Exception | None = None
        for attempt in range(3):
            try:
                response = await _client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=1200,
                    response_format={"type": "json_object"},
                    timeout=30.0,
                )
                result_text = response.choices[0].message.content.strip()
                risk_assessment = json.loads(result_text)
                usage = getattr(response, "usage", None)
                logger.info(
                    "clause_risk_scorer.ok type=%s model=%s in_tokens=%s out_tokens=%s",
                    clause_type, settings.OPENAI_MODEL,
                    getattr(usage, "prompt_tokens", "?"),
                    getattr(usage, "completion_tokens", "?"),
                )
                return {
                    "success": True,
                    "risk_score": risk_assessment.get("risk_score", 0),
                    "risk_factors": risk_assessment.get("risk_factors", []),
                    "landlord_favorable": risk_assessment.get("landlord_favorable", False),
                    "tenant_favorable": risk_assessment.get("tenant_favorable", False),
                    "summary": risk_assessment.get("summary", ""),
                    "recommendations": risk_assessment.get("recommendations", []),
                }
            except json.JSONDecodeError as e:
                logger.error("clause_risk_scorer.json_decode_error type=%s: %s", clause_type, e)
                return self._rule_based_score(clause_type, clause_text)
            except Exception as e:
                last_err = e
                logger.warning("clause_risk_scorer.retry type=%s attempt=%d err=%s", clause_type, attempt + 1, e)
                await asyncio.sleep(0.5 * (2 ** attempt))

        logger.error("clause_risk_scorer.exhausted type=%s err=%s", clause_type, last_err)
        return self._rule_based_score(clause_type, clause_text)

    async def score_multiple_clauses(self, clauses: list[dict]) -> list[dict]:
        """Score multiple clauses in parallel."""
        tasks = [self.score_clause(c["type"], c["text"]) for c in clauses]
        return await asyncio.gather(*tasks)


scorer = ClauseRiskScorer()
