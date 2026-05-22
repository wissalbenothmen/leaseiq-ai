import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import { BookOpen, Flag, Sparkles, Filter } from "lucide-react";
import { apiClient } from "../api/client";
import { labelClauseType } from "../utils/formatLabel";
import { Badge, Button, Card, EmptyState, RiskBadge } from "../components/ui";
import { AiSummary } from "../components/ui/AiSummary";

type RiskFilter = "all" | "high" | "medium" | "low";

export function ClausesPage() {
  const queryClient = useQueryClient();
  const [selectedLease, setSelectedLease] = useState<string>("");
  const [filter, setFilter] = useState<RiskFilter>("all");

  const { data: leasesData } = useQuery({
    queryKey: ["leases"],
    queryFn: () => apiClient.listLeases(),
  });

  const leases = (leasesData?.data || []) as any[];

  // Auto-select the first lease so the page never lands empty
  useEffect(() => {
    if (!selectedLease && leases.length > 0) setSelectedLease(leases[0].id);
  }, [leases, selectedLease]);

  const { data: clausesData, isLoading } = useQuery({
    queryKey: ["clauses", selectedLease],
    queryFn: () => apiClient.listClausesByLease(selectedLease),
    enabled: !!selectedLease,
  });

  const allClauses = (clausesData?.data || []) as any[];

  const filteredClauses = useMemo(() => {
    if (filter === "high")   return allClauses.filter((c) => c.risk_score >= 70);
    if (filter === "medium") return allClauses.filter((c) => c.risk_score >= 40 && c.risk_score < 70);
    if (filter === "low")    return allClauses.filter((c) => c.risk_score < 40);
    return allClauses;
  }, [allClauses, filter]);

  const highRisk = allClauses.filter((c) => c.risk_score >= 70);
  const medRisk  = allClauses.filter((c) => c.risk_score >= 40 && c.risk_score < 70);
  const lowRisk  = allClauses.filter((c) => c.risk_score < 40);
  const avgRisk = allClauses.length
    ? Math.round(allClauses.reduce((s, c) => s + c.risk_score, 0) / allClauses.length)
    : 0;

  const analyzeAllMutation = useMutation({
    mutationFn: () => apiClient.analyzeAllClauses(selectedLease),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["clauses", selectedLease] });
      toast.success("All clauses re-analyzed");
    },
    onError: () => toast.error("Re-analysis failed"),
  });

  const analyzeSingleMutation = useMutation({
    mutationFn: (clauseId: string) => apiClient.analyzeClause(clauseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["clauses", selectedLease] });
      toast.success("Clause re-analyzed");
    },
    onError: () => toast.error("Re-analysis failed"),
  });

  const selectedLeaseObj = leases.find((l) => l.id === selectedLease);

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-indigo-100 flex items-center justify-center">
            <BookOpen size={22} className="text-indigo-600" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Lease Clauses</h1>
            <p className="text-sm text-gray-500 mt-0.5 flex items-center gap-1.5">
              <Sparkles size={14} className="text-indigo-500" />
              AI-scored risk analysis across every clause
            </p>
          </div>
        </div>
        {selectedLease && allClauses.length > 0 && (
          <Button
            variant="primary"
            onClick={() => analyzeAllMutation.mutate()}
            disabled={analyzeAllMutation.isPending}
          >
            <Sparkles size={14} />
            {analyzeAllMutation.isPending ? "Analyzing…" : "Re-analyze all"}
          </Button>
        )}
      </div>

      {/* Lease selector */}
      <Card className="p-5">
        <div className="flex gap-4 items-center flex-wrap">
          <label className="text-sm font-medium text-gray-700 shrink-0">Lease</label>
          <select
            value={selectedLease}
            onChange={(e) => setSelectedLease(e.target.value)}
            className="flex-1 min-w-64 max-w-2xl px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent focus:outline-none bg-white"
          >
            {leases.map((l) => (
              <option key={l.id} value={l.id}>{l.tenant_name} — {l.property_address}</option>
            ))}
          </select>
          {selectedLeaseObj && (
            <Badge variant="brand">{leases.find((l) => l.id === selectedLease)?.lease_type}</Badge>
          )}
        </div>
      </Card>

      {!selectedLease && (
        <EmptyState
          icon={<BookOpen size={20} />}
          title="Select a lease to analyze"
          description="Choose a lease above to see AI-scored clause risk, factors, and recommendations."
        />
      )}

      {selectedLease && isLoading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      )}

      {selectedLease && !isLoading && allClauses.length === 0 && (
        <EmptyState title="No clauses for this lease yet" description="Upload a lease document to trigger AI clause extraction." />
      )}

      {allClauses.length > 0 && (
        <>
          {/* Risk summary bar — filterable */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <button
              onClick={() => setFilter("all")}
              className={`text-left rounded-xl border p-4 transition ${filter === "all" ? "border-indigo-500 bg-indigo-50/50 ring-2 ring-indigo-200" : "border-gray-200 bg-white hover:border-gray-300"}`}
            >
              <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">All clauses</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{allClauses.length}</p>
              <p className="text-xs text-gray-400 mt-1">Avg risk score {avgRisk}</p>
            </button>
            <button
              onClick={() => setFilter("high")}
              className={`text-left rounded-xl border p-4 transition ${filter === "high" ? "border-red-400 bg-red-50/70 ring-2 ring-red-200" : "border-red-100 bg-red-50/40 hover:border-red-300"}`}
            >
              <p className="text-xs text-red-700 font-medium uppercase tracking-wider">High risk (≥70)</p>
              <p className="text-2xl font-bold text-red-600 mt-1">{highRisk.length}</p>
              <p className="text-xs text-red-500/80 mt-1">Action recommended</p>
            </button>
            <button
              onClick={() => setFilter("medium")}
              className={`text-left rounded-xl border p-4 transition ${filter === "medium" ? "border-amber-400 bg-amber-50/70 ring-2 ring-amber-200" : "border-amber-100 bg-amber-50/40 hover:border-amber-300"}`}
            >
              <p className="text-xs text-amber-700 font-medium uppercase tracking-wider">Medium (40–69)</p>
              <p className="text-2xl font-bold text-amber-700 mt-1">{medRisk.length}</p>
              <p className="text-xs text-amber-600/80 mt-1">Watch &amp; negotiate</p>
            </button>
            <button
              onClick={() => setFilter("low")}
              className={`text-left rounded-xl border p-4 transition ${filter === "low" ? "border-emerald-400 bg-emerald-50/70 ring-2 ring-emerald-200" : "border-emerald-100 bg-emerald-50/40 hover:border-emerald-300"}`}
            >
              <p className="text-xs text-emerald-700 font-medium uppercase tracking-wider">Low (&lt;40)</p>
              <p className="text-2xl font-bold text-emerald-700 mt-1">{lowRisk.length}</p>
              <p className="text-xs text-emerald-600/80 mt-1">Favorable terms</p>
            </button>
          </div>

          {filter !== "all" && (
            <div className="flex items-center justify-between text-sm text-gray-500">
              <span className="flex items-center gap-1.5"><Filter size={14} /> Showing {filteredClauses.length} {filter}-risk clauses</span>
              <button onClick={() => setFilter("all")} className="text-indigo-600 hover:text-indigo-800 font-medium">Clear filter</button>
            </div>
          )}

          {/* Clause list */}
          <div className="space-y-4">
            {filteredClauses.map((clause) => (
              <Card key={clause.id} className="overflow-hidden">
                <Card.Body className="pt-6">
                  <div className="flex items-start justify-between gap-4 mb-3 flex-wrap">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-semibold text-gray-900">{labelClauseType(clause.clause_type)}</h3>
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
                    <div className="flex items-center gap-2 shrink-0">
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => analyzeSingleMutation.mutate(clause.id)}
                        disabled={analyzeSingleMutation.isPending}
                      >
                        <Sparkles size={12} /> Re-analyze
                      </Button>
                      <Button size="sm" variant="ghost" aria-label="Flag clause for review">
                        <Flag size={12} /> Flag
                      </Button>
                    </div>
                  </div>

                  <blockquote className="text-sm text-gray-600 italic border-l-2 border-gray-300 pl-4 mb-1">
                    “{clause.extracted_text}”
                  </blockquote>

                  <AiSummary
                    summary={clause.ai_summary}
                    recommendations={clause.ai_recommendations}
                    factors={clause.risk_factors}
                    analyzedAt={clause.ai_analyzed_at}
                  />
                </Card.Body>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
