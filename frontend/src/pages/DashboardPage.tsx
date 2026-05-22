import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell,
} from "recharts";
import {
  LayoutDashboard, FileText, AlertTriangle, Clock, CalendarDays, Sparkles, TrendingUp, ArrowRight,
} from "lucide-react";

import { apiClient } from "../api/client";
import { labelClauseType } from "../utils/formatLabel";
import { SkeletonCard } from "../components/SkeletonCard";
import { Card, KpiCard, Button } from "../components/ui";
import { AiBadge } from "../components/ui/AiSummary";

const CHART_DANGER = "#EF4444";
const CHART_MED = "#F59E0B";
const CHART_LOW = "#10B981";
const CHART_WARN = "#F59E0B";

export function DashboardPage() {
  const navigate = useNavigate();

  const { data: riskData } = useQuery({
    queryKey: ["portfolio-risk"],
    queryFn: () => apiClient.getPortfolioRiskSummary(),
  });
  const { data: expiringData, isLoading: expiringLoading } = useQuery({
    queryKey: ["expiring-leases"],
    queryFn: () => apiClient.getExpiringLeases(365),
  });
  const { data: complianceData, isLoading: complianceLoading } = useQuery({
    queryKey: ["obligation-compliance"],
    queryFn: () => apiClient.getObligationCompliance(),
  });
  const { data: statusData } = useQuery({
    queryKey: ["lease-status"],
    queryFn: () => apiClient.getLeaseStatusDistribution(),
  });

  const kpiLoading = expiringLoading || complianceLoading;

  const risk = riskData?.data;
  const expiring = expiringData?.data;
  const compliance = complianceData?.data;
  const status = statusData?.data;

  const overdueCount = compliance?.overdue_count ?? 0;
  const complianceRate = compliance?.compliance_rate ?? 100;
  const showAlert = overdueCount > 0 || complianceRate < 50;
  const totalLeases = (status?.distribution || []).reduce((s: number, d: any) => s + d.count, 0);
  const activeLeases = (status?.distribution || []).find((d: any) => d.status === "active")?.count ?? 0;

  // ── AI Briefing (deterministic insights derived from live data) ─────────────
  const briefing = useMemo(() => {
    const lines: { tone: "danger" | "warning" | "info"; text: string }[] = [];
    const highRiskTypes = (risk?.summary || [])
      .filter((s: any) => s.avg_risk_score >= 70)
      .sort((a: any, b: any) => b.avg_risk_score - a.avg_risk_score);
    if (highRiskTypes.length > 0) {
      const top = highRiskTypes[0];
      lines.push({
        tone: "danger",
        text: `Highest portfolio risk: ${labelClauseType(top.clause_type)} (avg ${Math.round(top.avg_risk_score)}/100, ${top.clause_count} clauses). Review indemnification + cap language across affected leases.`,
      });
    }
    const expiringSoon = (expiring?.leases || []).filter((l: any) => l.days_until_expiry <= 90);
    if (expiringSoon.length > 0) {
      lines.push({
        tone: "warning",
        text: `${expiringSoon.length} lease${expiringSoon.length === 1 ? "" : "s"} expir${expiringSoon.length === 1 ? "es" : "e"} within 90 days. Renewal-option windows are closing — confirm notice deadlines for ${expiringSoon.slice(0, 2).map((l: any) => l.tenant_name).join(", ")}.`,
      });
    }
    if (overdueCount > 0) {
      lines.push({
        tone: "danger",
        text: `${overdueCount} obligation${overdueCount === 1 ? " is" : "s are"} overdue. Compliance rate ${complianceRate.toFixed(1)}% — escalate to responsible party.`,
      });
    }
    if (lines.length === 0) {
      lines.push({
        tone: "info",
        text: `Portfolio looks healthy: ${activeLeases} active lease${activeLeases === 1 ? "" : "s"}, compliance at ${complianceRate.toFixed(1)}%. Next critical window in ${(expiring?.leases?.[0]?.days_until_expiry ?? "—")} days.`,
      });
    }
    return lines.slice(0, 3);
  }, [risk, expiring, overdueCount, complianceRate, activeLeases]);

  return (
    <div className="space-y-8 p-8">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-indigo-600/10 flex items-center justify-center">
            <LayoutDashboard size={22} className="text-indigo-600" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Portfolio Dashboard</h1>
            <p className="text-sm text-gray-500 mt-0.5">Real-time lease portfolio analytics &amp; AI risk assessment</p>
          </div>
        </div>
        <div className="flex items-center gap-3 text-sm text-gray-500">
          <span className="inline-flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Live
          </span>
          <span>{new Date().toLocaleDateString("en-US", { weekday: "long", month: "short", day: "numeric" })}</span>
        </div>
      </div>

      {/* AI Briefing — always visible, derived from live portfolio data */}
      <div className="relative overflow-hidden rounded-2xl border border-indigo-200 bg-gradient-to-br from-indigo-50 via-white to-violet-50 p-6 shadow-sm">
        <div className="absolute -right-12 -top-12 w-48 h-48 bg-indigo-200/30 rounded-full blur-3xl"></div>
        <div className="absolute -left-12 -bottom-12 w-48 h-48 bg-violet-200/30 rounded-full blur-3xl"></div>
        <div className="relative">
          <div className="flex items-center gap-2 mb-3">
            <AiBadge>AI Briefing</AiBadge>
            <span className="text-xs text-gray-500">Updated {new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}</span>
          </div>
          <ul className="space-y-2">
            {briefing.map((line, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-800">
                <span className={`mt-1.5 inline-block w-1.5 h-1.5 rounded-full shrink-0 ${
                  line.tone === "danger" ? "bg-red-500" : line.tone === "warning" ? "bg-amber-500" : "bg-indigo-500"
                }`}></span>
                <span className="leading-relaxed">{line.text}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {showAlert && (
        <div className="flex items-center justify-between gap-4 bg-red-50 border border-red-200 rounded-xl px-5 py-4">
          <div className="flex items-center gap-3">
            <AlertTriangle size={20} className="text-red-500 shrink-0" />
            <div>
              <p className="font-semibold text-red-800 text-sm">
                Compliance rate critically low — {complianceRate.toFixed(1)}%
              </p>
              <p className="text-red-700 text-xs mt-0.5">
                {overdueCount} obligation{overdueCount !== 1 ? "s are" : " is"} overdue and require immediate attention.
              </p>
            </div>
          </div>
          <Button variant="danger" onClick={() => navigate("/obligations")}>
            View overdue <ArrowRight size={14} />
          </Button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiLoading ? (
          <><SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard /></>
        ) : (
          <>
            <KpiCard
              title="Total Leases"
              value={totalLeases}
              sub={`${activeLeases} active`}
              variant="info"
              icon={<FileText size={20} />}
            />
            <KpiCard
              title="Expiring (1 Year)"
              value={expiring?.expiring_count || 0}
              sub="renewal windows"
              variant="warning"
              icon={<CalendarDays size={20} />}
              onClick={() => navigate("/analytics")}
            />
            <KpiCard
              title="Compliance Rate"
              value={`${complianceRate.toFixed(1)}%`}
              sub={`${compliance?.completed ?? 0} of ${compliance?.total_obligations ?? 0} done`}
              variant={complianceRate < 50 ? "critical" : complianceRate < 80 ? "warning" : "success"}
              icon={<TrendingUp size={20} />}
            />
            <KpiCard
              title="Overdue"
              value={overdueCount}
              sub="needs attention"
              variant={overdueCount > 0 ? "critical" : "success"}
              icon={<AlertTriangle size={20} />}
              onClick={() => navigate("/obligations")}
            />
          </>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RiskChart data={risk?.summary || []} />
        <ExpiringLeasesChart data={expiring?.leases || []} />
      </div>
    </div>
  );
}

function RiskChart({ data }: { data: any[] }) {
  const chartData = data.map((d) => ({ ...d, clause_type: labelClauseType(d.clause_type) }));
  return (
    <Card>
      <Card.Header>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-gray-900 flex items-center gap-2">
              Risk by Clause Type <AiBadge>AI</AiBadge>
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">Average risk score (0–100) across the portfolio</p>
          </div>
        </div>
      </Card.Header>
      <Card.Body>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 60, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
            <XAxis dataKey="clause_type" angle={-30} textAnchor="end" tick={{ fontSize: 11, fill: "#6b7280" }} interval={0} height={70} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#6b7280" }} />
            <Tooltip formatter={(val: any) => [`${val}`, "Avg risk"]} contentStyle={{ borderRadius: 8, border: "1px solid #e5e7eb" }} />
            <Legend
              verticalAlign="top"
              align="right"
              iconType="square"
              wrapperStyle={{ fontSize: 11, paddingBottom: 4 }}
              payload={[
                { value: "High ≥70", type: "square", color: CHART_DANGER },
                { value: "Medium 40–69", type: "square", color: CHART_MED },
                { value: "Low <40", type: "square", color: CHART_LOW },
              ]}
            />
            <Bar dataKey="avg_risk_score" radius={[4, 4, 0, 0]}>
              {chartData.map((entry: any, i: number) => (
                <Cell key={i} fill={entry.avg_risk_score >= 70 ? CHART_DANGER : entry.avg_risk_score >= 40 ? CHART_MED : CHART_LOW} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card.Body>
    </Card>
  );
}

function ExpiringLeasesChart({ data }: { data: any[] }) {
  const chartData = data.slice(0, 10).map((l) => ({
    name: l.tenant_name.length > 18 ? l.tenant_name.slice(0, 18) + "…" : l.tenant_name,
    days: l.days_until_expiry,
  }));
  return (
    <Card>
      <Card.Header>
        <h2 className="text-base font-semibold text-gray-900">Leases Expiring Soon</h2>
        <p className="text-xs text-gray-500 mt-0.5">Days until lease expiry — sorted soonest first</p>
      </Card.Header>
      <Card.Body>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 60, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
            <XAxis dataKey="name" angle={-30} textAnchor="end" tick={{ fontSize: 11, fill: "#6b7280" }} interval={0} height={70} />
            <YAxis tick={{ fontSize: 11, fill: "#6b7280" }} />
            <Tooltip formatter={(val: any) => [`${val} days`, "Until expiry"]} contentStyle={{ borderRadius: 8, border: "1px solid #e5e7eb" }} />
            <Bar dataKey="days" fill={CHART_WARN} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card.Body>
    </Card>
  );
}
