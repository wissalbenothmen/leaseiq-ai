/**
 * formatLabel.ts
 * Shared display-label utilities for converting backend snake_case identifiers
 * into human-readable Title Case strings across the entire UI.
 */

// ── Obligation types ──────────────────────────────────────────────────────────
const OBLIGATION_TYPE_LABELS: Record<string, string> = {
  rent_payment: "Rent Payment",
  inspection: "Inspection",
  one_time: "One-Time",
  maintenance: "Maintenance",
  insurance: "Insurance",
  insurance_renewal: "Insurance Renewal",
  cam_reconciliation: "CAM Reconciliation",
  tax_payment: "Tax Payment",
  utility_payment: "Utility Payment",
};

// ── Recurrence labels ─────────────────────────────────────────────────────────
const RECURRENCE_LABELS: Record<string, string> = {
  one_time: "One-Time",
  monthly: "Monthly",
  quarterly: "Quarterly",
  annual: "Annual",
  semi_annual: "Semi-Annual",
  bi_annual: "Bi-Annual",
};

// ── Lease type labels ─────────────────────────────────────────────────────────
const LEASE_TYPE_LABELS: Record<string, string> = {
  gross: "Gross",
  net: "Net",
  modified_gross: "Modified Gross",
  percentage: "Percentage",
  office: "Office",
  retail: "Retail",
  industrial: "Industrial",
  medical: "Medical",
  triple_net: "Triple Net",
  double_net: "Double Net",
};

// ── Clause type labels ────────────────────────────────────────────────────────
const CLAUSE_TYPE_LABELS: Record<string, string> = {
  rent_escalation: "Rent Escalation",
  termination: "Termination",
  renewal_option: "Renewal Option",
  cam_charges: "CAM Charges",
  maintenance: "Maintenance",
  subletting: "Subletting",
  insurance: "Insurance",
  assignment: "Assignment",
  holdover: "Holdover",
  parking: "Parking",
  use_clause: "Use Clause",
};

// ── Critical date type labels ─────────────────────────────────────────────────
const DATE_TYPE_LABELS: Record<string, string> = {
  renewal_notice: "Renewal Notice",
  rent_review: "Rent Review",
  lease_expiry: "Lease Expiry",
  option_exercise: "Option Exercise",
  rent_commencement: "Rent Commencement",
  break_option: "Break Option",
};

/**
 * Generic snake_case → Title Case fallback.
 * Splits on underscores, capitalises each word.
 */
function snakeToTitle(raw: string): string {
  return raw
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Human-readable label for an obligation type. */
export function labelObligationType(raw: string): string {
  return OBLIGATION_TYPE_LABELS[raw] ?? snakeToTitle(raw);
}

/** Human-readable label for a recurrence value. */
export function labelRecurrence(raw: string): string {
  return RECURRENCE_LABELS[raw] ?? snakeToTitle(raw);
}

/** Human-readable label for a lease type. */
export function labelLeaseType(raw: string): string {
  return LEASE_TYPE_LABELS[raw] ?? snakeToTitle(raw);
}

/** Human-readable label for a clause type. */
export function labelClauseType(raw: string): string {
  return CLAUSE_TYPE_LABELS[raw] ?? snakeToTitle(raw);
}

/** Human-readable label for a critical date type. */
export function labelDateType(raw: string): string {
  return DATE_TYPE_LABELS[raw] ?? snakeToTitle(raw);
}

/** USD currency formatter — no cents, e.g. "$1,234". */
export function formatUSD(amount: number): string {
  return amount.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  });
}
