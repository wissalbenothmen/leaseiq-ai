"""LeaseIQ AI — demo data seeder.

Drops and recreates the SQLite schema, then loads a realistic commercial
lease portfolio: 9 leases across diverse industries / locations / lease types,
each with 5-7 risk-scored clauses (with AI summary + recommendations already
populated so every screen shows substance without running OpenAI), 3-5
obligations distributed across overdue/upcoming/completed, and 2-4 critical
dates.

Run:
    python seed_data.py
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import text

from app.auth import hash_password
from app.database import Base, engine, AsyncSessionLocal
from app.models.user import User
from app.models.lease import CommercialLease
from app.models.lease_clause import LeaseClause
from app.models.obligation import Obligation
from app.models.critical_date import CriticalDate
from app.models.audit_log import AuditLog  # noqa: F401 — register table
from app.models.clause_query import ClauseQuery  # noqa: F401
from app.models.lease_document import LeaseDocument  # noqa: F401


TODAY = date.today()
NOW = datetime.now(timezone.utc).replace(tzinfo=None)


def _d(offset_days: int) -> date:
    return TODAY + timedelta(days=offset_days)


# ── Users ──────────────────────────────────────────────────────────────────────

USERS = [
    {
        "email": "admin@leaseiq.demo",
        "password": "Admin123!",
        "full_name": "Demo Admin",
        "role": "portfolio_manager",
    },
    {
        "email": "analyst@leaseiq.demo",
        "password": "Analyst123!",
        "full_name": "Sarah Chen",
        "role": "analyst",
    },
    {
        "email": "viewer@leaseiq.demo",
        "password": "Viewer123!",
        "full_name": "Mark Patel",
        "role": "viewer",
    },
]


# ── Leases ─────────────────────────────────────────────────────────────────────

LEASES = [
    {
        "tenant_name": "Helios Software Inc",
        "landlord_name": "Pacific Tower Holdings LP",
        "property_address": "Tower One, Floor 14 — 100 Market St, San Francisco, CA 94105",
        "lease_type": "gross",
        "term_start": _d(-365 * 2),
        "term_end": _d(365 * 4 + 90),
        "base_rent": 38500.00,
        "rent_escalation_pct": 3.0,
        "suite_number": "Floor 14",
        "square_footage": 12400.0,
        "status": "active",
        "notes": "Anchor tenant. Custom build-out for engineering floor. Indemnification clause renegotiated 2024.",
    },
    {
        "tenant_name": "Coastal Logistics Co",
        "landlord_name": "Newark Industrial Park LLC",
        "property_address": "Building B — 500 Industrial Way, Newark, NJ 07105",
        "lease_type": "net",
        "term_start": _d(-365 * 3),
        "term_end": _d(365 * 2 - 45),
        "base_rent": 22000.00,
        "rent_escalation_pct": 2.5,
        "suite_number": "Building B",
        "square_footage": 32500.0,
        "status": "active",
        "notes": "Triple-net with tenant-paid utilities. CAM reconciliation due Q2.",
    },
    {
        "tenant_name": "Brewhouse & Co",
        "landlord_name": "Plaza Retail Trust",
        "property_address": "Retail Bay 14 — 2200 Plaza Ave, Austin, TX 78701",
        "lease_type": "gross",
        "term_start": _d(-365 * 4),
        "term_end": _d(95),
        "base_rent": 8200.00,
        "rent_escalation_pct": 3.5,
        "suite_number": "Bay 14",
        "square_footage": 2800.0,
        "status": "active",
        "notes": "Restaurant tenant. Expiring soon — renewal option window open.",
    },
    {
        "tenant_name": "Beacon Analytics LLC",
        "landlord_name": "Federal Quarter Realty",
        "property_address": "Suite 600 — 25 Federal St, Boston, MA 02110",
        "lease_type": "gross",
        "term_start": _d(-365 * 3),
        "term_end": _d(60),
        "base_rent": 14200.00,
        "rent_escalation_pct": 3.0,
        "suite_number": "Suite 600",
        "square_footage": 4100.0,
        "status": "active",
        "notes": "Renewal decision required within 60 days.",
    },
    {
        "tenant_name": "Pacific Aero Services",
        "landlord_name": "Long Beach Aviation Partners",
        "property_address": "Hangar 4 — 1500 Skyway Blvd, Long Beach, CA 90802",
        "lease_type": "triple_net",
        "term_start": _d(-365 * 5),
        "term_end": _d(30),
        "base_rent": 27500.00,
        "rent_escalation_pct": 2.0,
        "suite_number": "Hangar 4",
        "square_footage": 18000.0,
        "status": "active",
        "notes": "Specialized aviation use — environmental clause is high-risk.",
    },
    {
        "tenant_name": "Triangle Biotech Inc",
        "landlord_name": "Research Triangle Properties",
        "property_address": "Building C — 800 Innovation Dr, Raleigh, NC 27607",
        "lease_type": "gross",
        "term_start": _d(-180),
        "term_end": _d(365 * 5 + 90),
        "base_rent": 31200.00,
        "rent_escalation_pct": 3.25,
        "suite_number": "Building C",
        "square_footage": 14800.0,
        "status": "active",
        "notes": "Newest tenant. Lab fit-out completed. Personal guarantee uncapped — flagged.",
    },
    {
        "tenant_name": "Atlantic Wealth Group",
        "landlord_name": "Crescent Avenue Realty",
        "property_address": "Penthouse — 99 Crescent Ave, Miami, FL 33131",
        "lease_type": "gross",
        "term_start": _d(-365 * 4),
        "term_end": _d(10),
        "base_rent": 19800.00,
        "rent_escalation_pct": 3.0,
        "suite_number": "Penthouse",
        "square_footage": 5600.0,
        "status": "active",
        "notes": "Imminent expiry — landlord verbal indication of renewal at +12% rent.",
    },
    {
        "tenant_name": "Northstar Retail Group",
        "landlord_name": "Midtown Plaza Holdings",
        "property_address": "Storefront 12 — 450 Madison Ave, New York, NY 10022",
        "lease_type": "percentage",
        "term_start": _d(-365 * 6),
        "term_end": _d(-30),
        "base_rent": 41000.00,
        "rent_escalation_pct": 4.0,
        "suite_number": "Storefront 12",
        "square_footage": 3200.0,
        "status": "expired",
        "notes": "Expired — holdover negotiations underway.",
    },
    {
        "tenant_name": "Cascade Cloud Services",
        "landlord_name": "Seattle Tech Campus LLC",
        "property_address": "East Wing — 1200 Westlake Ave N, Seattle, WA 98109",
        "lease_type": "modified_gross",
        "term_start": _d(-365 * 1),
        "term_end": _d(365 * 6),
        "base_rent": 52000.00,
        "rent_escalation_pct": 3.5,
        "suite_number": "East Wing",
        "square_footage": 22000.0,
        "status": "active",
        "notes": "Strategic anchor — data center floor with redundant power obligations.",
    },
]


# ── Clause templates ───────────────────────────────────────────────────────────

CLAUSE_TEMPLATES = {
    "personal_guarantee_high": {
        "clause_type": "personal_guarantee",
        "extracted_text": "Tenant's principal executes a continuing personal guarantee for all obligations of the Tenant under this Lease, without cap and without limitation as to time.",
        "risk_score": 92,
        "risk_factors": ["uncapped personal liability", "indefinite duration", "no burn-down"],
        "landlord_favorable": "true",
        "tenant_favorable": "false",
        "confidence_score": 0.94,
        "ai_summary": "Uncapped personal guarantee — the principal is personally liable for all lease obligations without limit or sunset. This is the highest-risk clause type in commercial leases and creates unlimited personal financial exposure.",
        "ai_recommendations": [
            "Negotiate an absolute cap equal to 12 months base rent",
            "Add a 24-month burn-down provision contingent on payment history",
            "Replace the guarantee with a letter of credit or enhanced security deposit",
            "Add a release trigger upon corporate creditworthiness milestones",
        ],
    },
    "cam_uncapped": {
        "clause_type": "cam_charges",
        "extracted_text": "Tenant shall pay its pro-rata share of all Common Area Maintenance expenses, with no cap on annual increases and no exclusions for capital expenditures.",
        "risk_score": 78,
        "risk_factors": ["uncapped CAM escalation", "no capex exclusions", "open-ended operating cost exposure"],
        "landlord_favorable": "true",
        "tenant_favorable": "false",
        "confidence_score": 0.91,
        "ai_summary": "Uncapped CAM with no exclusions for capital expenditures. The landlord can pass through any operating cost — including major capex like roof replacement — without limit, creating significant unmodeled financial exposure.",
        "ai_recommendations": [
            "Negotiate a 3-5% hard cap on controllable CAM increases",
            "Exclude capital expenditures, management fees above 3%, and landlord overhead",
            "Request annual audit rights with 12-month look-back",
            "Add gross-up at 95% occupancy to normalize per-tenant calculations",
        ],
    },
    "cam_capped": {
        "clause_type": "cam_charges",
        "extracted_text": "CAM charges are capped at 4% annual increase on controllable expenses. Capital expenditures and taxes pass through at actual cost.",
        "risk_score": 40,
        "risk_factors": ["controllable expenses capped", "capex passed through at actual"],
        "landlord_favorable": "false",
        "tenant_favorable": "false",
        "confidence_score": 0.93,
        "ai_summary": "CAM with a 4% controllable cap is market-standard for institutional landlords. Passes capex and taxes at actual cost — model these separately when forecasting occupancy cost.",
        "ai_recommendations": [
            "Confirm 'controllable' excludes utilities, snow, security",
            "Add audit right and 12-month dispute window",
            "Carve out capital improvements that benefit the landlord exclusively",
        ],
    },
    "renewal_market": {
        "clause_type": "renewal_option",
        "extracted_text": "Tenant has the option to renew for two consecutive 5-year terms at fair market rent, with 12 months' written notice required prior to expiration.",
        "risk_score": 18,
        "risk_factors": ["FMR-based renewal", "12 month notice", "two extension options"],
        "landlord_favorable": "false",
        "tenant_favorable": "true",
        "confidence_score": 0.96,
        "ai_summary": "Fair market rent renewal with two 5-year options is the standard best-practice structure. Provides tenure protection while ensuring market-aligned economics for both sides.",
        "ai_recommendations": [
            "Define FMR determination method (broker survey, appraisal, or negotiation)",
            "Add a ceiling: renewal rent cannot exceed expiring rent by more than 15%",
            "Confirm option survives assignment to affiliates",
        ],
    },
    "indemnification_broad": {
        "clause_type": "indemnification",
        "extracted_text": "Tenant shall indemnify, defend and hold harmless Landlord from any and all claims, regardless of cause, arising in or about the Premises.",
        "risk_score": 72,
        "risk_factors": ["indemnification regardless of cause", "no carve-out for landlord negligence"],
        "landlord_favorable": "true",
        "tenant_favorable": "false",
        "confidence_score": 0.88,
        "ai_summary": "Broad indemnification with no carve-out for landlord negligence shifts substantial liability to the tenant — including claims caused by the landlord's own acts. This is unenforceable in some jurisdictions but creates real defense costs.",
        "ai_recommendations": [
            "Carve out claims arising from landlord's negligence or willful misconduct",
            "Limit indemnity to claims caused by tenant's use of the premises",
            "Require landlord to maintain commercial general liability of $5M+",
            "Add mutual indemnification with parallel landlord obligation",
        ],
    },
    "environmental_full": {
        "clause_type": "environmental",
        "extracted_text": "Tenant assumes full responsibility for any environmental contamination on or about the Premises during the Term, regardless of cause or pre-existing condition.",
        "risk_score": 84,
        "risk_factors": ["full environmental liability", "pre-existing contamination included", "uncapped remediation cost"],
        "landlord_favorable": "true",
        "tenant_favorable": "false",
        "confidence_score": 0.90,
        "ai_summary": "Environmental clause requires tenant to assume liability for contamination regardless of cause — including pre-existing conditions. Potential exposure can run into millions for state-ordered cleanup. Phase I assessment is essential before signing.",
        "ai_recommendations": [
            "Limit liability to contamination caused by tenant during the term",
            "Commission Phase I ESA before signing to document baseline",
            "Negotiate mutual indemnification for pre-existing contamination",
            "Cap remediation liability at insurance proceeds plus a defined ceiling",
        ],
    },
    "subletting_restricted": {
        "clause_type": "assignment_subletting",
        "extracted_text": "Tenant may not sublet or assign without Landlord's prior written consent. 50% of any sublease profit reverts to Landlord.",
        "risk_score": 65,
        "risk_factors": ["consent required", "50% profit-share to landlord", "no deemed-approval timeline"],
        "landlord_favorable": "true",
        "tenant_favorable": "false",
        "confidence_score": 0.92,
        "ai_summary": "Subletting requires consent with a 50% profit-share. The combination materially reduces the economic value of any sublease and limits flexibility during downturns or restructuring.",
        "ai_recommendations": [
            "Negotiate profit-share down to 25% (more market-standard)",
            "Define 'consent not unreasonably withheld' with 30-day deemed approval",
            "Carve out corporate affiliate transfers and restructuring",
            "Reserve right to share net (not gross) sublease profit",
        ],
    },
    "operating_expense": {
        "clause_type": "operating_expenses",
        "extracted_text": "Tenant pays a proportionate share of operating expenses including utilities, maintenance, insurance, and property taxes, escalated annually by CPI plus 2%.",
        "risk_score": 58,
        "risk_factors": ["CPI plus fixed escalation", "no controllable cap", "tax pass-through"],
        "landlord_favorable": "true",
        "tenant_favorable": "false",
        "confidence_score": 0.89,
        "ai_summary": "CPI + 2% creates compounded escalation that can outpace market rents over a multi-year term. Lock CPI to a specific index and seek a controllable-expense cap.",
        "ai_recommendations": [
            "Specify the CPI index (CPI-U All Urban, base year locked at signing)",
            "Negotiate annual cap of 4% on controllable expenses",
            "Exclude landlord's overhead and management fees above market",
        ],
    },
    "exclusive_use": {
        "clause_type": "exclusive_use",
        "extracted_text": "Landlord shall not lease space within the property to any business primarily engaged in the same line of business as Tenant during the Term.",
        "risk_score": 28,
        "risk_factors": ["protected exclusivity", "competitor prohibition"],
        "landlord_favorable": "false",
        "tenant_favorable": "true",
        "confidence_score": 0.94,
        "ai_summary": "Exclusive-use protection prevents the landlord from leasing to direct competitors within the same property. Strong tenant-favorable provision for retail and specialty operators.",
        "ai_recommendations": [
            "Define 'primarily engaged' with revenue percentage threshold (e.g., >40%)",
            "Add remedy for breach (rent abatement or termination right)",
            "Survive landlord transfer of the property",
        ],
    },
    "termination_for_cause": {
        "clause_type": "termination_for_cause",
        "extracted_text": "Either party may terminate upon material breach with 30 days' written notice and cure period. Early termination fee equal to 6 months' base rent plus unamortized tenant improvements.",
        "risk_score": 48,
        "risk_factors": ["6-month penalty", "unamortized TI included", "cure period present"],
        "landlord_favorable": "false",
        "tenant_favorable": "false",
        "confidence_score": 0.87,
        "ai_summary": "Termination-for-cause is balanced with a meaningful cure period. The 6-month + unamortized TI exit penalty is moderate. Confirm the TI amortization schedule before signing.",
        "ai_recommendations": [
            "Reduce penalty step-down: 100% Y1-2, 75% Y3-4, 50% thereafter",
            "Confirm straight-line TI amortization method",
            "Add landlord mitigation obligation if replacement tenant found",
        ],
    },
}


def lease_clauses_for(lease_index: int) -> list[dict]:
    """Return a curated list of clauses for each lease — tuned to make the demo varied."""
    profiles = {
        0: ["renewal_market", "indemnification_broad", "cam_capped", "operating_expense", "exclusive_use"],
        1: ["cam_uncapped", "environmental_full", "operating_expense", "subletting_restricted", "termination_for_cause"],
        2: ["renewal_market", "cam_capped", "exclusive_use", "operating_expense", "termination_for_cause", "subletting_restricted"],
        3: ["personal_guarantee_high", "cam_capped", "renewal_market", "indemnification_broad", "operating_expense"],
        4: ["environmental_full", "cam_uncapped", "operating_expense", "indemnification_broad", "termination_for_cause"],
        5: ["personal_guarantee_high", "indemnification_broad", "cam_capped", "renewal_market", "operating_expense", "exclusive_use"],
        6: ["renewal_market", "cam_capped", "operating_expense", "termination_for_cause"],
        7: ["cam_uncapped", "subletting_restricted", "operating_expense", "indemnification_broad", "termination_for_cause"],
        8: ["renewal_market", "cam_capped", "exclusive_use", "indemnification_broad", "operating_expense", "termination_for_cause", "subletting_restricted"],
    }
    return [CLAUSE_TEMPLATES[name] for name in profiles.get(lease_index, [])]


# ── Obligations ────────────────────────────────────────────────────────────────

def obligations_for(lease_index: int, lease_id: uuid.UUID, base_rent: float) -> list[dict]:
    """Mix of overdue / due-soon / completed obligations to make the dashboard interesting."""
    common = [
        {
            "obligation_type": "rent_payment",
            "due_date": _d(-5),
            "recurrence": "monthly",
            "status": "completed",
            "amount": base_rent,
            "description": f"Base rent — paid {(_d(-5)).strftime('%b %Y')}",
            "responsible_party": "Tenant",
        },
        {
            "obligation_type": "rent_payment",
            "due_date": _d(26),
            "recurrence": "monthly",
            "status": "pending",
            "amount": base_rent,
            "description": "Next month base rent",
            "responsible_party": "Tenant",
        },
    ]
    variants = [
        [
            {"obligation_type": "estoppel_certificate", "due_date": _d(7), "recurrence": "one_time", "status": "pending", "description": "Quarterly estoppel certification request", "responsible_party": "Tenant"},
            {"obligation_type": "security_deposit_review", "due_date": _d(28), "recurrence": "annual", "status": "pending", "description": "Annual security deposit review and adjustment", "responsible_party": "Landlord"},
        ],
        [
            {"obligation_type": "rent_escalation_letter", "due_date": _d(-78), "recurrence": "annual", "status": "pending", "description": "Annual CPI escalation notice — overdue", "responsible_party": "Landlord"},
            {"obligation_type": "operating_expense_statement", "due_date": _d(-33), "recurrence": "annual", "status": "pending", "description": "OpEx reconciliation statement — overdue", "responsible_party": "Landlord"},
        ],
        [
            {"obligation_type": "renewal_notice", "due_date": _d(14), "recurrence": "one_time", "status": "pending", "description": "Renewal option notice deadline", "responsible_party": "Tenant"},
            {"obligation_type": "insurance_renewal", "due_date": _d(45), "recurrence": "annual", "status": "pending", "description": "Annual liability insurance renewal", "responsible_party": "Tenant"},
        ],
        [
            {"obligation_type": "cam_reconciliation", "due_date": _d(60), "recurrence": "annual", "status": "pending", "description": "Annual CAM reconciliation", "responsible_party": "Landlord"},
            {"obligation_type": "maintenance_inspection", "due_date": _d(90), "recurrence": "quarterly", "status": "pending", "description": "Quarterly HVAC maintenance inspection", "responsible_party": "Tenant"},
        ],
        [
            {"obligation_type": "environmental_audit", "due_date": _d(-12), "recurrence": "annual", "status": "pending", "description": "Annual environmental compliance audit — overdue", "responsible_party": "Tenant"},
            {"obligation_type": "tax_certificate", "due_date": _d(20), "recurrence": "annual", "status": "pending", "description": "Property tax certificate filing", "responsible_party": "Landlord"},
        ],
    ]
    return common + variants[lease_index % len(variants)]


# ── Critical Dates ─────────────────────────────────────────────────────────────

def critical_dates_for(lease_index: int, term_start: date, term_end: date) -> list[dict]:
    days_to_expiry = (term_end - TODAY).days
    common = [
        {"date_type": "lease_expiration", "date_value": term_end, "days_until": days_to_expiry, "alert_sent": "false"},
    ]
    if days_to_expiry > 365:
        common.append({"date_type": "mid_term_review", "date_value": _d(180), "days_until": 180, "alert_sent": "false"})
    if 0 < days_to_expiry <= 365:
        notice_date = term_end - timedelta(days=180)
        common.append({"date_type": "renewal_option_notice", "date_value": notice_date, "days_until": (notice_date - TODAY).days, "alert_sent": "true" if (notice_date - TODAY).days < 60 else "false"})
    common.append({"date_type": "rent_escalation", "date_value": _d(45), "days_until": 45, "alert_sent": "false"})
    if lease_index in (4, 5):
        common.append({"date_type": "environmental_review", "date_value": _d(-7), "days_until": -7, "alert_sent": "true"})
    return common


# ── Seed runner ────────────────────────────────────────────────────────────────

async def reset_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def seed() -> None:
    print(">>> Dropping and recreating schema...")
    await reset_schema()

    async with AsyncSessionLocal() as db:
        # Users
        print(">>> Seeding users...")
        for u in USERS:
            db.add(User(
                email=u["email"],
                hashed_password=hash_password(u["password"]),
                full_name=u["full_name"],
                role=u["role"],
                is_active="true",
            ))
        await db.commit()

        # Leases + nested data
        print(">>> Seeding leases, clauses, obligations, critical dates...")
        for i, ld in enumerate(LEASES):
            lease = CommercialLease(
                tenant_name=ld["tenant_name"],
                landlord_name=ld["landlord_name"],
                property_address=ld["property_address"],
                lease_type=ld["lease_type"],
                term_start=ld["term_start"],
                term_end=ld["term_end"],
                base_rent=ld["base_rent"],
                rent_escalation_pct=ld["rent_escalation_pct"],
                suite_number=ld["suite_number"],
                square_footage=ld["square_footage"],
                status=ld["status"],
                notes=ld["notes"],
            )
            db.add(lease)
            await db.flush()  # populate lease.id

            for c in lease_clauses_for(i):
                db.add(LeaseClause(
                    lease_id=lease.id,
                    clause_type=c["clause_type"],
                    extracted_text=c["extracted_text"],
                    risk_score=c["risk_score"],
                    risk_factors=c["risk_factors"],
                    landlord_favorable=c["landlord_favorable"],
                    tenant_favorable=c["tenant_favorable"],
                    confidence_score=c["confidence_score"],
                    ai_summary=c["ai_summary"],
                    ai_recommendations=c["ai_recommendations"],
                    ai_analyzed_at=NOW,
                ))

            for o in obligations_for(i, lease.id, ld["base_rent"]):
                db.add(Obligation(
                    lease_id=lease.id,
                    obligation_type=o["obligation_type"],
                    due_date=o["due_date"],
                    recurrence=o["recurrence"],
                    status=o["status"],
                    amount=o.get("amount"),
                    description=o.get("description"),
                    responsible_party=o.get("responsible_party"),
                ))

            for d in critical_dates_for(i, ld["term_start"], ld["term_end"]):
                db.add(CriticalDate(
                    lease_id=lease.id,
                    date_type=d["date_type"],
                    date_value=d["date_value"],
                    days_until=d["days_until"],
                    alert_sent=d["alert_sent"],
                ))

        await db.commit()

    # Summary
    async with AsyncSessionLocal() as db:
        for tbl in ("users", "commercial_leases", "lease_clauses", "obligations", "critical_dates"):
            r = await db.execute(text(f"SELECT COUNT(*) FROM {tbl}"))
            print(f"  {tbl}: {r.scalar()}")

    print(">>> Seed complete.")
    print()
    print("Login credentials:")
    for u in USERS:
        print(f"  {u['role']:<20} {u['email']:<30} {u['password']}")


if __name__ == "__main__":
    asyncio.run(seed())
