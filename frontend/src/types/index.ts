export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "tenant" | "landlord" | "lease_admin" | "real_estate_attorney" | "portfolio_manager" | "admin";
  is_active: string;
  created_at: string;
}

export interface CommercialLease {
  id: string;
  property_address: string;
  tenant_name: string;
  landlord_name: string;
  lease_type: "gross" | "net" | "modified_gross" | "percentage";
  term_start: string;
  term_end: string;
  base_rent?: number;
  rent_escalation_pct?: number;
  status: "active" | "expired" | "pending" | "terminated";
  suite_number?: string;
  square_footage?: number;
  created_at: string;
  updated_at: string;
}

export interface LeaseClause {
  id: string;
  lease_id: string;
  clause_type: string;
  extracted_text: string;
  risk_score: number;
  risk_factors?: string[];
  landlord_favorable: string;
  tenant_favorable: string;
  confidence_score?: number;
  ai_summary?: string | null;
  ai_recommendations?: string[] | null;
  ai_analyzed_at?: string | null;
  created_at: string;
}

export interface Obligation {
  id: string;
  lease_id: string;
  obligation_type: string;
  due_date: string;
  recurrence: "monthly" | "annual" | "one_time";
  status: "pending" | "completed" | "overdue";
  amount?: number;
  description?: string;
  responsible_party?: string;
  created_at: string;
}

export interface CriticalDate {
  id: string;
  lease_id: string;
  date_type: string;
  date_value: string;
  days_until?: number;
  alert_sent: string;
  created_at: string;
}

export interface PortfolioRiskSummary {
  summary: Array<{
    clause_type: string;
    avg_risk_score: number;
    clause_count: number;
  }>;
}

export interface ExpiringLeaseInfo {
  id: string;
  tenant_name: string;
  property_address: string;
  term_end: string;
  days_until_expiry: number;
}

export interface ExpiringLeasesResponse {
  expiring_count: number;
  leases: ExpiringLeaseInfo[];
}

export interface ComplianceSummary {
  total_obligations: number;
  completed: number;
  compliance_rate: number;
  overdue_count: number;
  upcoming_30_days: number;
}

export interface LeaseRiskBreakdown {
  lease_id: string;
  total_clauses: number;
  avg_risk_score: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  clauses: Array<{
    id: string;
    clause_type: string;
    risk_score: number;
    landlord_favorable: string;
    tenant_favorable: string;
  }>;
}
