import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { apiClient } from "../api/client";
import {
  labelObligationType,
  labelRecurrence,
  labelClauseType,
  labelDateType,
  labelLeaseType,
  formatUSD,
} from "../utils/formatLabel";
import { Badge, RiskBadge, Button } from "../components/ui";
import { AiSummary } from "../components/ui/AiSummary";

export function LeaseDetailPage() {
  const { leaseId } = useParams<{ leaseId: string }>();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"overview" | "clauses" | "obligations" | "dates">("overview");
  const [analyzeResult, setAnalyzeResult] = useState<any>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [voiceRunning, setVoiceRunning] = useState(false);
  const [voiceResult, setVoiceResult] = useState<any>(null);
  const [briefDownloading, setBriefDownloading] = useState(false);

  const runVoiceCrossValidate = async () => {
    if (!leaseId) return;
    setVoiceRunning(true);
    setVoiceResult(null);
    try {
      const r = await apiClient.voiceCrossValidateLease(leaseId);
      setVoiceResult(r.data);
    } catch (e: any) {
      setVoiceResult({ status: "error", detail: e?.response?.data?.detail || "Cross-validation failed" });
    } finally {
      setVoiceRunning(false);
    }
  };

  const downloadTenantBriefing = async () => {
    if (!leaseId) return;
    setBriefDownloading(true);
    try {
      const r = await apiClient.downloadTenantBriefingPdf(leaseId);
      const blob = new Blob([r.data], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      const disp = (r.headers?.["content-disposition"] as string | undefined) || "";
      const m = disp.match(/filename="?([^";]+)"?/);
      link.download = m?.[1] ?? `leaseiq-tenant-briefing-${leaseId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } finally {
      setBriefDownloading(false);
    }
  };

  const { data, isLoading } = useQuery({
    queryKey: ["lease-detail", leaseId],
    queryFn: () => apiClient.getLeaseDetail(leaseId!),
    enabled: !!leaseId,
  });

  const detail = data?.data;

  const analyzeAllMutation = useMutation({
    mutationFn: () => apiClient.analyzeAllClauses(leaseId!),
    onMutate: () => setAnalyzing(true),
    onSuccess: (res) => {
      setAnalyzeResult(res.data);
      setAnalyzing(false);
      queryClient.invalidateQueries({ queryKey: ["lease-detail", leaseId] });
    },
    onError: () => setAnalyzing(false),
  });

  const analyzeSingleMutation = useMutation({
    mutationFn: (clauseId: string) => apiClient.analyzeClause(clauseId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["lease-detail", leaseId] }),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="p-8">
        <p className="text-red-600">Lease not found.</p>
        <Link to="/leases" className="text-indigo-600 hover:underline mt-2 block">← Back to Leases</Link>
      </div>
    );
  }

  const { lease, clauses, obligations, critical_dates, summary } = detail;

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link to="/leases" className="text-sm text-indigo-600 hover:text-indigo-800 flex items-center gap-1 mb-2">
            ← Back to Leases
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">{lease.tenant_name}</h1>
          <p className="text-gray-500 mt-1">{lease.property_address}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
          lease.status === "active" ? "bg-green-100 text-green-800" :
          lease.status === "expired" ? "bg-red-100 text-red-800" :
          "bg-gray-100 text-gray-800"
        }`}>
          {lease.status.charAt(0).toUpperCase() + lease.status.slice(1)}
        </span>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[
          { label: "Clause Count", value: summary.clause_count, color: "indigo" },
          { label: "Avg Risk Score", value: summary.avg_risk_score, color: summary.avg_risk_score >= 60 ? "red" : summary.avg_risk_score >= 40 ? "yellow" : "green" },
          { label: "High Risk Clauses", value: summary.high_risk_clauses, color: "red" },
          { label: "Overdue Obligations", value: summary.overdue_obligations, color: "orange" },
          { label: "Upcoming Dates (90d)", value: summary.upcoming_dates, color: "blue" },
        ].map((c) => (
          <div key={c.label} className={`bg-white rounded-xl border border-gray-100 shadow-sm p-4`}>
            <p className="text-xs text-gray-500 font-medium">{c.label}</p>
            <p className={`text-2xl font-bold mt-1 ${
              c.color === "red" ? "text-red-600" :
              c.color === "yellow" ? "text-yellow-600" :
              c.color === "green" ? "text-green-600" :
              c.color === "orange" ? "text-orange-600" :
              "text-indigo-600"
            }`}>{c.value}</p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-1">
          {(["overview", "clauses", "obligations", "dates"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition ${
                activeTab === tab
                  ? "border-indigo-600 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
              {tab === "clauses" && <span className="ml-1 text-xs bg-gray-100 px-1.5 py-0.5 rounded-full">{clauses.length}</span>}
              {tab === "obligations" && <span className="ml-1 text-xs bg-gray-100 px-1.5 py-0.5 rounded-full">{obligations.length}</span>}
              {tab === "dates" && <span className="ml-1 text-xs bg-gray-100 px-1.5 py-0.5 rounded-full">{critical_dates.length}</span>}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab: Overview */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">Lease Details</h2>
            {[
              ["Landlord", lease.landlord_name],
              ["Lease Type", labelLeaseType(lease.lease_type)],
              ["Suite", lease.suite_number || "—"],
              ["Square Footage", lease.square_footage ? `${lease.square_footage.toLocaleString()} sq ft` : "—"],
              ["Term Start", new Date(lease.term_start).toLocaleDateString()],
              ["Term End", new Date(lease.term_end).toLocaleDateString()],
              ["Base Rent", lease.base_rent ? `${formatUSD(lease.base_rent)}/mo` : "—"],
              ["Escalation", lease.rent_escalation_pct ? `${lease.rent_escalation_pct}% / year` : "—"],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between text-sm">
                <span className="text-gray-500 font-medium">{label}</span>
                <span className="text-gray-900">{value}</span>
              </div>
            ))}
            {lease.notes && (
              <div className="pt-2 border-t border-gray-100">
                <p className="text-xs text-gray-400 font-medium mb-1">Notes</p>
                <p className="text-sm text-gray-700">{lease.notes}</p>
              </div>
            )}
          </div>

          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">AI Risk Assessment</h2>
            {clauses.length === 0 ? (
              <p className="text-sm text-gray-500">No clauses added yet.</p>
            ) : (
              <>
                <div className="space-y-2 mb-4">
                  {clauses.slice(0, 5).map((c: any) => (
                    <div key={c.id} className="flex items-center justify-between text-sm">
                      <span className="text-gray-700">{labelClauseType(c.clause_type)}</span>
                      <RiskBadge score={c.risk_score} />
                    </div>
                  ))}
                  {clauses.length > 5 && <p className="text-xs text-gray-400">+{clauses.length - 5} more clauses</p>}
                </div>
                <button
                  onClick={() => analyzeAllMutation.mutate()}
                  disabled={analyzing}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 text-white text-sm font-medium rounded-lg transition"
                >
                  {analyzing ? (
                    <><span className="animate-spin">⏳</span> Analyzing...</>
                  ) : (
                    <><span>🤖</span> Run AI Analysis on All Clauses</>
                  )}
                </button>
              </>
            )}

            {analyzeResult && (
              <div className="mt-4 p-4 bg-indigo-50 rounded-lg border border-indigo-200">
                <p className="text-sm font-semibold text-indigo-800 mb-2">
                  ✅ Analyzed {analyzeResult.analyzed} clauses
                </p>
                {analyzeResult.results.map((r: any) => (
                  <div key={r.clause_id} className="mb-3 text-xs">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-gray-800">{labelClauseType(r.clause_type)}</span>
                      <RiskBadge score={r.risk_score} />
                    </div>
                    {r.summary && <p className="text-gray-600 mb-1">{r.summary}</p>}
                    {r.recommendations?.length > 0 && (
                      <ul className="list-disc list-inside text-gray-600 space-y-0.5">
                        {r.recommendations.map((rec: string, i: number) => <li key={i}>{rec}</li>)}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Voice ↔ Lease Cross-Validation */}
            <div className="mt-6 pt-4 border-t border-gray-100">
              <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2 mb-1">
                🎙️ Voice ↔ Lease Cross-Validation
              </h3>
              <p className="text-xs text-gray-500 mb-3">
                Compares the tenant's voice query against lease clauses + duration/percent conflicts and renders the tenant briefing PDF.
              </p>
              <div className="flex gap-2 flex-wrap">
                <button
                  onClick={runVoiceCrossValidate}
                  disabled={voiceRunning}
                  className="flex-1 min-w-[140px] flex items-center justify-center gap-2 px-3 py-2 bg-violet-600 hover:bg-violet-700 disabled:bg-gray-400 text-white text-xs font-medium rounded-lg transition"
                >
                  {voiceRunning ? <><span className="animate-spin">⏳</span> Cross-validating…</> : <>🎙️ Cross-Validate Voice</>}
                </button>
                <button
                  onClick={downloadTenantBriefing}
                  disabled={briefDownloading}
                  className="flex-1 min-w-[140px] flex items-center justify-center gap-2 px-3 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-400 text-white text-xs font-medium rounded-lg transition"
                >
                  {briefDownloading ? <><span className="animate-spin">⏳</span> Exporting…</> : <>📄 Tenant Briefing PDF</>}
                </button>
              </div>
              {voiceResult && voiceResult.status === "no_query" && (
                <p className="mt-3 text-xs text-gray-500">No clause query / voice transcript on file. Capture one from /clauses first.</p>
              )}
              {voiceResult && voiceResult.status === "error" && (
                <p className="mt-3 text-xs text-red-600">{voiceResult.detail}</p>
              )}
              {voiceResult && voiceResult.status === "completed" && (
                <div className="mt-3 p-3 bg-violet-50 border border-violet-200 rounded-lg">
                  <div className="flex gap-3 flex-wrap text-xs">
                    {voiceResult.recommendation && (
                      <span className="px-2 py-1 bg-violet-100 text-violet-800 rounded-full font-bold">
                        {voiceResult.recommendation}
                      </span>
                    )}
                    {Array.isArray(voiceResult.duration_window_conflicts) && (
                      <span className="text-violet-700">{voiceResult.duration_window_conflicts.length} duration conflict(s)</span>
                    )}
                    {Array.isArray(voiceResult.percent_conflicts) && (
                      <span className="text-violet-700">{voiceResult.percent_conflicts.length} percent conflict(s)</span>
                    )}
                    {Array.isArray(voiceResult.ambiguity_flags) && (
                      <span className="text-violet-700">{voiceResult.ambiguity_flags.length} ambiguity flag(s)</span>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab: Clauses */}
      {activeTab === "clauses" && (
        <div className="space-y-4">
          {clauses.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-12 text-center">
              <p className="text-gray-500">No clauses found for this lease.</p>
            </div>
          ) : (
            clauses.map((clause: any) => (
              <div key={clause.id} className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
                <div className="flex items-start justify-between mb-3 gap-3 flex-wrap">
                  <div>
                    <h3 className="font-semibold text-gray-900">{labelClauseType(clause.clause_type)}</h3>
                    <div className="flex gap-2 mt-1 flex-wrap">
                      <RiskBadge score={clause.risk_score} />
                      {clause.landlord_favorable === "true" && (
                        <Badge variant="warning" size="sm">Landlord favorable</Badge>
                      )}
                      {clause.tenant_favorable === "true" && (
                        <Badge variant="info" size="sm">Tenant favorable</Badge>
                      )}
                      {clause.confidence_score && (
                        <Badge variant="neutral" size="sm">{Math.round(clause.confidence_score * 100)}% confidence</Badge>
                      )}
                    </div>
                  </div>
                  <Button size="sm" variant="secondary" onClick={() => analyzeSingleMutation.mutate(clause.id)} disabled={analyzeSingleMutation.isPending}>
                    Re-analyze
                  </Button>
                </div>
                <blockquote className="text-sm text-gray-600 italic border-l-2 border-gray-300 pl-3 mb-1">
                  “{clause.extracted_text}”
                </blockquote>
                <AiSummary
                  summary={clause.ai_summary}
                  recommendations={clause.ai_recommendations}
                  factors={clause.risk_factors}
                  analyzedAt={clause.ai_analyzed_at}
                />
              </div>
            ))
          )}
        </div>
      )}

      {/* Tab: Obligations */}
      {activeTab === "obligations" && (
        <div className="space-y-3">
          {obligations.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-12 text-center">
              <p className="text-gray-500">No obligations for this lease.</p>
            </div>
          ) : (
            obligations.map((o: any) => {
              const daysUntil = Math.ceil((new Date(o.due_date).getTime() - Date.now()) / 86400000);
              const isOverdue = daysUntil < 0;
              const statusLabel = isOverdue && o.status !== "completed" ? "overdue" : o.status;
              return (
                <div key={o.id} className={`bg-white rounded-xl border shadow-sm p-4 ${isOverdue && o.status !== "completed" ? "border-red-200 bg-red-50" : "border-gray-100"}`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{labelObligationType(o.obligation_type)}</p>
                      <div className="flex gap-4 mt-1 text-sm text-gray-500">
                        <span>Due: {new Date(o.due_date).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })}</span>
                        {o.amount && <span>{formatUSD(o.amount)}/mo</span>}
                        {o.recurrence && <span>{labelRecurrence(o.recurrence)}</span>}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        statusLabel === "completed" ? "bg-green-100 text-green-800" :
                        statusLabel === "overdue" ? "bg-red-100 text-red-800" :
                        "bg-yellow-100 text-yellow-800"
                      }`}>{statusLabel.charAt(0).toUpperCase() + statusLabel.slice(1)}</span>
                      <p className={`text-xs mt-1 ${isOverdue && o.status !== "completed" ? "text-red-600 font-medium" : "text-gray-500"}`}>
                        {isOverdue && o.status !== "completed" ? `${Math.abs(daysUntil)}d overdue` : `${daysUntil}d left`}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Tab: Critical Dates */}
      {activeTab === "dates" && (
        <div className="space-y-3">
          {critical_dates.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-12 text-center">
              <p className="text-gray-500">No critical dates for this lease.</p>
            </div>
          ) : (
            critical_dates.map((d: any) => (
              <div key={d.id} className={`bg-white rounded-xl border shadow-sm p-4 ${d.days_until !== null && d.days_until <= 30 ? "border-amber-200 bg-amber-50" : "border-gray-100"}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{labelDateType(d.date_type)}</p>
                    <p className="text-sm text-gray-500 mt-1">{new Date(d.date_value).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}</p>
                  </div>
                  <div className="text-right">
                    {d.days_until !== null && (
                      <span className={`text-sm font-semibold ${
                        d.days_until < 0 ? "text-red-600" :
                        d.days_until <= 30 ? "text-amber-600" :
                        d.days_until <= 90 ? "text-blue-600" :
                        "text-gray-600"
                      }`}>
                        {d.days_until < 0 ? `${Math.abs(d.days_until)}d past` :
                         d.days_until === 0 ? "Today" :
                         `${d.days_until}d away`}
                      </span>
                    )}
                    {d.alert_sent === "true" && (
                      <p className="text-xs text-green-600 mt-1">✓ Alert sent</p>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
