import { ReactNode } from "react";

type Variant = "neutral" | "success" | "warning" | "danger" | "info" | "brand";
type Size = "sm" | "md";

const VARIANTS: Record<Variant, string> = {
  neutral: "bg-gray-100 text-gray-700",
  success: "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200",
  warning: "bg-amber-50 text-amber-700 ring-1 ring-amber-200",
  danger:  "bg-red-50 text-red-700 ring-1 ring-red-200",
  info:    "bg-sky-50 text-sky-700 ring-1 ring-sky-200",
  brand:   "bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200",
};

const SIZES: Record<Size, string> = {
  sm: "px-2 py-0.5 text-[11px] font-semibold",
  md: "px-2.5 py-1 text-xs font-semibold",
};

export function Badge({
  variant = "neutral",
  size = "md",
  children,
  className = "",
}: {
  variant?: Variant;
  size?: Size;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full whitespace-nowrap ${VARIANTS[variant]} ${SIZES[size]} ${className}`}>
      {children}
    </span>
  );
}

export function RiskBadge({ score, size = "md" }: { score: number; size?: Size }) {
  if (score >= 70) return <Badge variant="danger" size={size}>{score} HIGH</Badge>;
  if (score >= 40) return <Badge variant="warning" size={size}>{score} MED</Badge>;
  return <Badge variant="success" size={size}>{score} LOW</Badge>;
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, Variant> = {
    active: "success",
    expired: "danger",
    pending: "warning",
    terminated: "neutral",
    completed: "success",
    overdue: "danger",
  };
  return <Badge variant={map[status] || "neutral"}>{status.charAt(0).toUpperCase() + status.slice(1)}</Badge>;
}
