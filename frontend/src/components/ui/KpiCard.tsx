import { ReactNode } from "react";

type Variant = "neutral" | "critical" | "warning" | "info" | "success";

const ACCENT: Record<Variant, { surface: string; value: string; ring: string }> = {
  neutral:  { surface: "bg-white",     value: "text-gray-900",     ring: "border-gray-200" },
  critical: { surface: "bg-red-50",    value: "text-red-600",      ring: "border-red-200 border-l-4 border-l-red-500" },
  warning:  { surface: "bg-amber-50",  value: "text-amber-700",    ring: "border-amber-200 border-l-4 border-l-amber-500" },
  info:     { surface: "bg-sky-50",    value: "text-sky-700",      ring: "border-sky-200 border-l-4 border-l-sky-500" },
  success:  { surface: "bg-emerald-50", value: "text-emerald-700", ring: "border-emerald-200 border-l-4 border-l-emerald-500" },
};

export function KpiCard({
  title,
  value,
  icon,
  sub,
  variant = "neutral",
  onClick,
}: {
  title: string;
  value: string | number;
  icon?: ReactNode;
  sub?: string;
  variant?: Variant;
  onClick?: () => void;
}) {
  const accent = ACCENT[variant];
  return (
    <div
      onClick={onClick}
      className={`relative rounded-xl border shadow-sm p-5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md ${accent.surface} ${accent.ring} ${onClick ? "cursor-pointer" : ""}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-gray-500 text-sm font-medium">{title}</p>
          <p className={`text-3xl font-bold mt-2 tabular-nums tracking-tight ${accent.value}`}>{value}</p>
          {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
        </div>
        {icon && <span className="ml-2 shrink-0 text-gray-400">{icon}</span>}
      </div>
    </div>
  );
}
