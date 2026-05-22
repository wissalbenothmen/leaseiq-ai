import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { FileText, Upload, Search, Building2, ArrowUpRight } from "lucide-react";

import { apiClient } from "../api/client";
import { labelLeaseType, formatUSD } from "../utils/formatLabel";
import { CommercialLease } from "../types";
import { Badge, Button, Card, EmptyState, StatusBadge } from "../components/ui";
import { KpiCard } from "../components/ui/KpiCard";

export function LeasesPage() {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [search, setSearch] = useState<string>("");

  const { data, isLoading } = useQuery({
    queryKey: ["leases", statusFilter, search],
    queryFn: () => apiClient.listLeases({
      status: statusFilter || undefined,
      tenant_name: search || undefined,
    }),
  });

  const allLeases = (data?.data || []) as CommercialLease[];
  const leases = typeFilter
    ? allLeases.filter((l) => l.lease_type === typeFilter)
    : allLeases;

  const { totalRent, expiringSoon } = useMemo(() => {
    let r = 0; let exp = 0;
    const now = Date.now();
    for (const l of leases) {
      if (l.base_rent) r += l.base_rent;
      const days = Math.ceil((new Date(l.term_end).getTime() - now) / 86400000);
      if (days >= 0 && days <= 180) exp++;
    }
    return { totalRent: r, expiringSoon: exp };
  }, [leases]);

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-indigo-100 flex items-center justify-center">
            <FileText size={22} className="text-indigo-600" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Leases</h1>
            <p className="text-sm text-gray-500 mt-0.5">Manage your commercial lease portfolio</p>
          </div>
        </div>
        <Button variant="primary" onClick={() => toast.success("Upload flow — coming next sprint")}>
          <Upload size={14} /> Upload &amp; analyze
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard
          title="Portfolio Size"
          value={allLeases.length}
          sub={`${allLeases.filter((l) => l.status === "active").length} active`}
          variant="info"
          icon={<Building2 size={18} />}
        />
        <KpiCard
          title="Monthly Base Rent"
          value={formatUSD(totalRent)}
          sub="Combined across filtered leases"
          variant="neutral"
        />
        <KpiCard
          title="Expiring (180 days)"
          value={expiringSoon}
          sub="Renewal decisions due"
          variant={expiringSoon > 0 ? "warning" : "success"}
        />
      </div>

      <Card className="p-5">
        <div className="flex gap-3 flex-wrap items-center">
          <div className="relative flex-1 min-w-64">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search tenants, properties…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent focus:outline-none text-sm"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-white"
          >
            <option value="">All status</option>
            <option value="active">Active</option>
            <option value="expired">Expired</option>
            <option value="pending">Pending</option>
            <option value="terminated">Terminated</option>
          </select>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-white"
          >
            <option value="">All types</option>
            <option value="gross">Gross</option>
            <option value="net">Net</option>
            <option value="triple_net">Triple Net</option>
            <option value="modified_gross">Modified Gross</option>
            <option value="percentage">Percentage</option>
          </select>
          {(search || statusFilter || typeFilter) && (
            <Button variant="ghost" size="sm" onClick={() => { setSearch(""); setStatusFilter(""); setTypeFilter(""); }}>
              Clear
            </Button>
          )}
        </div>
      </Card>

      {isLoading ? (
        <div className="text-center py-12 text-sm text-gray-500">Loading leases…</div>
      ) : leases.length === 0 ? (
        <EmptyState
          icon={<FileText size={20} />}
          title="No leases match your filters"
          description="Try clearing filters or upload a new lease document to get started."
        />
      ) : (
        <Card className="overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <Th>Tenant</Th>
                  <Th>Property</Th>
                  <Th>Type</Th>
                  <Th>Term end</Th>
                  <Th>Status</Th>
                  <Th align="right">Base rent</Th>
                  <Th></Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {leases.map((lease) => {
                  const daysToEnd = Math.ceil((new Date(lease.term_end).getTime() - Date.now()) / 86400000);
                  return (
                    <tr
                      key={lease.id}
                      onClick={() => navigate(`/leases/${lease.id}`)}
                      className="group hover:bg-indigo-50/40 cursor-pointer transition-colors"
                    >
                      <td className="px-6 py-4">
                        <div className="font-semibold text-gray-900">{lease.tenant_name}</div>
                        <div className="text-xs text-gray-500 mt-0.5">{lease.landlord_name}</div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-700">{lease.property_address}</td>
                      <td className="px-6 py-4">
                        <Badge variant="brand" size="sm">{labelLeaseType(lease.lease_type)}</Badge>
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <div className="text-gray-900">{new Date(lease.term_end).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}</div>
                        {daysToEnd > 0 && daysToEnd <= 180 && (
                          <div className="text-xs text-amber-600 mt-0.5">{daysToEnd}d remaining</div>
                        )}
                        {daysToEnd <= 0 && (
                          <div className="text-xs text-red-600 mt-0.5">expired</div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <StatusBadge status={lease.status} />
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 font-medium text-right tabular-nums">
                        {lease.base_rent ? <>{formatUSD(lease.base_rent)}<span className="text-gray-400">/mo</span></> : "—"}
                      </td>
                      <td className="px-4 py-4 text-right">
                        <ArrowUpRight size={16} className="text-gray-300 group-hover:text-indigo-600 transition-colors" />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}

function Th({ children, align = "left" }: { children?: React.ReactNode; align?: "left" | "right" }) {
  return (
    <th className={`px-6 py-3 text-${align} text-xs font-semibold uppercase tracking-wider text-gray-500`}>
      {children}
    </th>
  );
}
