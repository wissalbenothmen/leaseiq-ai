import React from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, Label,
} from "recharts";
import { labelClauseType } from "../utils/formatLabel";
import { BarChart3, FileText, AlertTriangle, Clock } from "lucide-react";

const BRAND_COLORS = ['#6366f1', '#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b'];

const ChartTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
      <p className="font-semibold text-gray-700 mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} style={{ color: p.color }} className="text-xs">
          {p.name}: <span className="font-medium">{typeof p.value === 'number' ? p.value.toLocaleString() : p.value}</span>
        </p>
      ))}
    </div>
  );
};

// Standardised 5-token chart palette — LeaseIQ brand colours.
// Blues / indigo / teal spectrum; avoids generic orange & green defaults.
const CHART_BRAND   = "#6366F1"; // indigo-500  — primary series / brand
const CHART_DANGER  = "#EF4444"; // red-500     — high risk / overdue
const CHART_WARNING = "#F59E0B"; // amber-500   — medium risk / expiring soon (retained for semantic clarity)
const CHART_SUCCESS = "#14B8A6"; // teal-500    — low risk / healthy (replaces green default)
const CHART_INFO    = "#3B82F6"; // blue-500    — neutral info series (replaces sky default)

// Status-distribution pie colours (semantically keyed to status names)
const STATUS_COLORS: Record<string, string> = {
  Active:     "#14B8A6", // teal-500   — healthy / active  (brand teal, not generic green)
  Expired:    "#EF4444", // red-500    — expired / danger
  Pending:    "#6366F1", // indigo-500 — pending / brand primary
  Terminated: "#94A3B8", // slate-400  — terminated / neutral
};
function statusColor(name: string, index: number): string {
  return STATUS_COLORS[name] ?? [CHART_BRAND, CHART_INFO, CHART_WARNING, CHART_DANGER][index % 4];
}

function MetricCard({ title, value, sub, color, icon }: { title: string; value: string | number; sub?: string; color?: string; icon?: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-500 font-medium">{title}</p>
          <p className={`text-3xl font-bold mt-1 ${color || "text-gray-900"}`}>{value}</p>
          {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
        </div>
        {icon && <span className="ml-2">{icon}</span>}
      </div>
    </div>
  );
}

export function AnalyticsPage() {
  const { data: riskData } = useQuery({
    queryKey: ["portfolio-risk"],
    queryFn: () => apiClient.getPortfolioRiskSummary(),
  });

  const { data: expiringData } = useQuery({
    queryKey: ["expiring-leases-365"],
    queryFn: () => apiClient.getExpiringLeases(365),
  });

  const { data: expiring3yr } = useQuery({
    queryKey: ["expiring-leases-1095"],
    queryFn: () => apiClient.getExpiringLeases(1095),
  });

  const { data: complianceData } = useQuery({
    queryKey: ["obligation-compliance"],
    queryFn: () => apiClient.getObligationCompliance(),
  });

  const { data: statusData } = useQuery({
    queryKey: ["lease-status"],
    queryFn: () => apiClient.getLeaseStatusDistribution(),
  });

  const risk = riskData?.data;
  const expiring = expiringData?.data;
  const expiring3 = expiring3yr?.data;
  const compliance = complianceData?.data;
  const statusDist = statusData?.data;

  const riskChartData = (risk?.summary || []).map((r: any) => ({
    name: labelClauseType(r.clause_type),
    risk: Math.round(r.avg_risk_score),
    count: r.clause_count,
  }));

  const statusChartData = (statusDist?.distribution || []).map((s: any) => ({
    name: s.status.charAt(0).toUpperCase() + s.status.slice(1),
    value: s.count,
  }));

  const expiringChartData = (expiring3?.leases || []).map((l: any) => ({
    name: l.tenant_name.length > 12 ? l.tenant_name.slice(0, 12) + "…" : l.tenant_name,
    days: l.days_until_expiry,
  })).sort((a: any, b: any) => a.days - b.days);

  const radarData = (risk?.summary || []).map((r: any) => ({
    subject: labelClauseType(r.clause_type),
    risk: Math.round(r.avg_risk_score),
    fullMark: 100,
  }));

  const totalLeases = (statusDist?.distribution || []).reduce((s: number, d: any) => s + d.count, 0);

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <div className="flex items-center gap-3">
        <BarChart3 size={30} className="text-purple-600" />
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Portfolio Analytics</h1>
          <p className="text-gray-500 mt-1">Real-time risk assessment and compliance tracking</p>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Total Leases"
          value={totalLeases}
          sub="in portfolio"
          icon={<FileText size={20} className="text-gray-300" />}
        />
        <MetricCard
          title="Expiring (1 Year)"
          value={expiring?.expiring_count ?? 0}
          sub="leases"
          color={expiring?.expiring_count > 0 ? "text-amber-600" : "text-green-600"}
          icon={<Clock size={20} className="text-gray-300" />}
        />
        <MetricCard
          title="Compliance Rate"
          value={`${(compliance?.compliance_rate ?? 0).toFixed(1)}%`}
          sub={`${compliance?.completed ?? 0} of ${compliance?.total_obligations ?? 0} obligations`}
          color={compliance?.compliance_rate >= 80 ? "text-green-600" : "text-red-600"}
          icon={<BarChart3 size={20} className="text-gray-300" />}
        />
        <MetricCard
          title="Overdue"
          value={compliance?.overdue_count ?? 0}
          sub="obligations"
          color={compliance?.overdue_count > 0 ? "text-red-600" : "text-green-600"}
          icon={<AlertTriangle size={20} className="text-gray-300" />}
        />
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk by clause type */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">Risk by Clause Type</h3>
          <p className="text-xs text-gray-400 mb-4">Average risk score (0–100) across all leases</p>
          {riskChartData.length === 0 ? (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">No clause data</div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={riskChartData} margin={{ top: 8, right: 16, bottom: 50, left: 8 }}>
                <CartesianGrid stroke="#f0f0f0" vertical={false} />
                <XAxis dataKey="name" angle={-35} textAnchor="end" tick={{ fontSize: 11, fill: '#6b7280' }} interval={0} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#6b7280' }}>
                  <Label value="Risk Score" angle={-90} position="insideLeft" style={{ fontSize: 11, fill: '#9ca3af' }} />
                </YAxis>
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="risk" name="Avg Risk" fill={CHART_DANGER} radius={[4, 4, 0, 0]}>
                  {riskChartData.map((_: any, i: number) => (
                    <Cell key={i} fill={
                      riskChartData[i].risk >= 70 ? CHART_DANGER :
                      riskChartData[i].risk >= 40 ? CHART_WARNING : CHART_SUCCESS
                    } />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Lease status pie */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">Lease Status Distribution</h3>
          <p className="text-xs text-gray-400 mb-4">Portfolio breakdown by lease status</p>
          {statusChartData.length === 0 ? (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">No data</div>
          ) : (
            <div className="flex items-center gap-4">
              <ResponsiveContainer width="60%" height={220}>
                <PieChart>
                  <Pie
                    data={statusChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={90}
                    dataKey="value"
                    paddingAngle={3}
                  >
                    {statusChartData.map((d: any, i: number) => (
                      <Cell key={i} fill={statusColor(d.name, i)} />
                    ))}
                  </Pie>
                  <Tooltip content={<ChartTooltip />} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2 flex-1">
                {statusChartData.map((d: any, i: number) => (
                  <div key={d.name} className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full inline-block" style={{ backgroundColor: statusColor(d.name, i) }}></span>
                    <span className="text-sm text-gray-700">{d.name}</span>
                    <span className="ml-auto text-sm font-semibold text-gray-900">{d.value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Expiring leases */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">Lease Expiry Timeline</h3>
          <p className="text-xs text-gray-400 mb-4">Days until expiry — next 3 years</p>
          {expiringChartData.length === 0 ? (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">No expiring leases</div>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={expiringChartData} layout="vertical" margin={{ top: 8, right: 16, bottom: 8, left: 10 }}>
                <CartesianGrid stroke="#f0f0f0" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11, fill: '#6b7280' }}>
                  <Label value="Days" position="insideBottom" offset={-2} style={{ fontSize: 11, fill: '#9ca3af' }} />
                </XAxis>
                <YAxis type="category" dataKey="name" width={90} tick={{ fontSize: 11, fill: '#6b7280' }} />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="days" name="Days until expiry" fill={CHART_WARNING} radius={[0, 4, 4, 0]}>
                  {expiringChartData.map((d: any, i: number) => (
                    <Cell key={i} fill={d.days <= 180 ? CHART_DANGER : d.days <= 365 ? CHART_WARNING : CHART_BRAND} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Risk radar */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">Clause Risk Radar</h3>
          <p className="text-xs text-gray-400 mb-4">Portfolio-wide risk profile by clause type</p>
          {radarData.length === 0 ? (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">No clause data</div>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#e5e7eb" />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: '#6b7280' }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 9, fill: '#9ca3af' }} />
                <Radar name="Risk Score" dataKey="risk" stroke={BRAND_COLORS[0]} fill={BRAND_COLORS[0]} fillOpacity={0.25} />
                <Tooltip content={<ChartTooltip />} />
              </RadarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Obligation Compliance Summary */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Obligation Compliance</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {[
            { label: "Total Obligations", value: compliance?.total_obligations ?? 0, color: "text-gray-900" },
            { label: "Completed", value: compliance?.completed ?? 0, color: "text-green-600" },
            { label: "Overdue", value: compliance?.overdue_count ?? 0, color: "text-red-600" },
            { label: "Upcoming (30d)", value: compliance?.upcoming_30_days ?? 0, color: "text-blue-600" },
          ].map((m) => (
            <div key={m.label} className="text-center">
              <p className={`text-4xl font-bold ${m.color}`}>{m.value}</p>
              <p className="text-sm text-gray-500 mt-1">{m.label}</p>
            </div>
          ))}
        </div>

        {/* Compliance bar */}
        {compliance?.total_obligations > 0 && (
          <div className="mt-6">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600 font-medium">Compliance Rate</span>
              <span className={`font-bold ${compliance.compliance_rate >= 80 ? "text-green-600" : "text-red-600"}`}>
                {compliance.compliance_rate.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all ${compliance.compliance_rate >= 80 ? "bg-green-500" : compliance.compliance_rate >= 50 ? "bg-yellow-500" : "bg-red-500"}`}
                style={{ width: `${compliance.compliance_rate}%` }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
