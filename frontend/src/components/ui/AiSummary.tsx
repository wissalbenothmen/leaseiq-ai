import { ReactNode } from "react";
import { Sparkles } from "lucide-react";

export function AiSummary({
  summary,
  recommendations,
  factors,
  analyzedAt,
  variant = "default",
}: {
  summary?: string | null;
  recommendations?: string[] | null;
  factors?: string[] | null;
  analyzedAt?: string | null;
  variant?: "default" | "compact";
}) {
  if (!summary && (!recommendations || recommendations.length === 0)) return null;

  const tone = variant === "compact"
    ? "bg-indigo-50/40 border-indigo-100"
    : "bg-gradient-to-br from-indigo-50/80 to-violet-50/60 border-indigo-200";

  return (
    <div className={`relative mt-3 border-l-2 border-l-indigo-500 ${tone} border rounded-r-lg p-4`}>
      <div className="flex items-center gap-2 mb-2">
        <span className="inline-flex items-center gap-1 text-[11px] font-bold uppercase tracking-wider text-indigo-700 bg-indigo-100 px-2 py-0.5 rounded-full">
          <Sparkles size={11} /> AI Analysis
        </span>
        {analyzedAt && (
          <span className="text-[11px] text-gray-400">
            {new Date(analyzedAt).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
          </span>
        )}
      </div>

      {summary && (
        <p className="text-sm text-gray-700 leading-relaxed">{summary}</p>
      )}

      {factors && factors.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {factors.map((f, i) => (
            <span key={i} className="px-2 py-0.5 bg-white/70 text-gray-700 rounded text-xs ring-1 ring-indigo-100">
              {f}
            </span>
          ))}
        </div>
      )}

      {recommendations && recommendations.length > 0 && (
        <div className="mt-3">
          <p className="text-[11px] font-bold uppercase tracking-wider text-indigo-700 mb-1.5">Recommendations</p>
          <ul className="space-y-1.5">
            {recommendations.map((r, i) => (
              <li key={i} className="text-sm text-gray-700 flex gap-2">
                <span className="text-indigo-500 shrink-0">→</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export function AiBadge({ children = "AI" }: { children?: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-indigo-700 bg-indigo-100 px-1.5 py-0.5 rounded-full">
      <Sparkles size={9} /> {children}
    </span>
  );
}
