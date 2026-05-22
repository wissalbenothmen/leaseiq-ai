import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import toast from "react-hot-toast";
import { CheckSquare, Plus, AlertTriangle, Clock, ListChecks } from "lucide-react";

import { apiClient } from "../api/client";
import { Obligation } from "../types";
import { labelObligationType, labelRecurrence, formatUSD } from "../utils/formatLabel";
import { Badge, Button, Card, EmptyState, KpiCard } from "../components/ui";

type Filter = "all" | "overdue" | "upcoming" | "pending";

export function ObligationsPage() {
  const [filter, setFilter] = useState<Filter>("all");
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: overdueData } = useQuery({
    queryKey: ["overdue-obligations"],
    queryFn: () => apiClient.getOverdueObligations(),
  });

  const { data: upcomingData } = useQuery({
    queryKey: ["upcoming-obligations"],
    queryFn: () => apiClient.getUpcomingObligations(30),
  });

  const completeMutation = useMutation({
    mutationFn: (obligationId: string) => apiClient.completeObligation(obligationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["overdue-obligations"] });
      queryClient.invalidateQueries({ queryKey: ["upcoming-obligations"] });
      setConfirmId(null);
      toast.success("Marked complete");
    },
    onError: () => toast.error("Could not save — try again"),
  });

  const overdue = (overdueData?.data || []) as Obligation[];
  const upcoming = (upcomingData?.data || []) as Obligation[];
  const visible = useMemo(() => {
    if (filter === "overdue") return overdue;
    if (filter === "upcoming") return upcoming;
    if (filter === "pending") return [...overdue, ...upcoming].filter((o) => o.status !== "completed");
    return [...overdue, ...upcoming];
  }, [filter, overdue, upcoming]);

  const totalAmount = useMemo(
    () => visible.reduce((s, o) => s + (o.amount || 0), 0),
    [visible],
  );

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {confirmId && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-xl p-6 max-w-sm w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Mark as complete?</h3>
            <p className="text-sm text-gray-600 mb-4">
              This action will mark the obligation as completed. The audit log will record who confirmed and when.
            </p>
            <div className="flex gap-3 justify-end">
              <Button variant="secondary" size="sm" onClick={() => setConfirmId(null)}>Cancel</Button>
              <Button variant="primary" size="sm" onClick={() => completeMutation.mutate(confirmId)} disabled={completeMutation.isPending}>
                {completeMutation.isPending ? "Saving…" : "Confirm complete"}
              </Button>
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center">
            <CheckSquare size={22} className="text-emerald-600" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Obligations</h1>
            <p className="text-sm text-gray-500 mt-0.5">Track lease-related obligations and deadlines</p>
          </div>
        </div>
        <Button variant="primary"><Plus size={14} /> Add obligation</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard title="Overdue" value={overdue.length} sub="Needs action" variant={overdue.length > 0 ? "critical" : "success"} icon={<AlertTriangle size={18} />} onClick={() => setFilter("overdue")} />
        <KpiCard title="Upcoming 30 days" value={upcoming.length} sub="Pending review" variant="warning" icon={<Clock size={18} />} onClick={() => setFilter("upcoming")} />
        <KpiCard title="Total in view" value={visible.length} sub={totalAmount > 0 ? `${formatUSD(totalAmount)} aggregated` : "—"} variant="info" icon={<ListChecks size={18} />} />
      </div>

      <div className="flex gap-2 flex-wrap">
        {(["all", "pending", "overdue", "upcoming"] as Filter[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
              filter === f
                ? "bg-indigo-600 text-white shadow-sm"
                : "bg-white text-gray-700 ring-1 ring-gray-300 hover:bg-gray-50"
            }`}
          >
            {f === "overdue" ? `Overdue (${overdue.length})` : f === "upcoming" ? `Upcoming (${upcoming.length})` : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {visible.length === 0 ? (
          <EmptyState title="Nothing in this view" description="No obligations match your selected filter." />
        ) : (
          visible.map((o) => <ObligationRow key={o.id} o={o} onComplete={() => setConfirmId(o.id)} />)
        )}
      </div>
    </div>
  );
}

function ObligationRow({ o, onComplete }: { o: Obligation; onComplete: () => void }) {
  const daysUntil = Math.ceil((new Date(o.due_date).getTime() - Date.now()) / 86400000);
  const isOverdue = daysUntil < 0;
  return (
    <Card className={`p-5 ${isOverdue ? "border-red-200 bg-red-50/50" : ""}`}>
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <h3 className="font-semibold text-gray-900">{labelObligationType(o.obligation_type)}</h3>
            {isOverdue ? (
              <Badge variant="danger" size="sm">{Math.abs(daysUntil)}d overdue</Badge>
            ) : daysUntil <= 14 ? (
              <Badge variant="warning" size="sm">{daysUntil}d remaining</Badge>
            ) : (
              <Badge variant="neutral" size="sm">{daysUntil}d remaining</Badge>
            )}
            <Badge variant="neutral" size="sm">{labelRecurrence(o.recurrence)}</Badge>
          </div>
          <div className="flex gap-4 text-sm text-gray-600 flex-wrap">
            <span>Due {new Date(o.due_date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}</span>
            {o.amount && <span className="tabular-nums">{formatUSD(o.amount)}</span>}
            {o.responsible_party && <span>· {o.responsible_party}</span>}
          </div>
          {o.description && <p className="text-xs text-gray-500 mt-1.5">{o.description}</p>}
        </div>
        <div className="shrink-0">
          {o.status !== "completed" ? (
            <Button variant="secondary" size="sm" onClick={onComplete}>Mark complete</Button>
          ) : (
            <Badge variant="success">Completed</Badge>
          )}
        </div>
      </div>
    </Card>
  );
}
