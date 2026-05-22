/**
 * ApiDocsPage.tsx
 * Branded API documentation page for LeaseIQ AI.
 * Embeds the backend's branded Swagger UI (/api/docs) in an iframe
 * and wraps it with LeaseIQ branding (dark sidebar, endpoint cards, indigo palette).
 */

const BASE_URL = "http://localhost:8022";

const ENDPOINT_GROUPS = [
  {
    tag: "Auth",
    color: "bg-sky-100 text-sky-800",
    dotColor: "bg-sky-500",
    endpoints: [
      { method: "POST", path: "/api/v1/auth/register", desc: "Register a new user account" },
      { method: "POST", path: "/api/v1/auth/token", desc: "Obtain a JWT bearer token" },
      { method: "GET",  path: "/api/v1/auth/me", desc: "Get the authenticated user profile" },
    ],
  },
  {
    tag: "Leases",
    color: "bg-indigo-100 text-indigo-800",
    dotColor: "bg-indigo-500",
    endpoints: [
      { method: "GET",    path: "/api/v1/leases",        desc: "List all leases with filters" },
      { method: "POST",   path: "/api/v1/leases",        desc: "Create a new commercial lease" },
      { method: "GET",    path: "/api/v1/leases/{id}",   desc: "Retrieve a single lease by ID" },
      { method: "PATCH",  path: "/api/v1/leases/{id}",   desc: "Update a lease's fields" },
      { method: "DELETE", path: "/api/v1/leases/{id}",   desc: "Delete a lease record" },
    ],
  },
  {
    tag: "Clauses",
    color: "bg-violet-100 text-violet-800",
    dotColor: "bg-violet-500",
    endpoints: [
      { method: "GET",  path: "/api/v1/clauses",       desc: "List clauses (filterable by lease)" },
      { method: "POST", path: "/api/v1/clauses",       desc: "Create a clause with AI risk scoring" },
      { method: "GET",  path: "/api/v1/clauses/{id}",  desc: "Retrieve clause detail + risk score" },
      { method: "PATCH", path: "/api/v1/clauses/{id}", desc: "Update clause text or risk score" },
      { method: "DELETE", path: "/api/v1/clauses/{id}", desc: "Remove a clause" },
    ],
  },
  {
    tag: "Obligations",
    color: "bg-teal-100 text-teal-800",
    dotColor: "bg-teal-500",
    endpoints: [
      { method: "GET",  path: "/api/v1/obligations",       desc: "List obligations, filter by status" },
      { method: "POST", path: "/api/v1/obligations",       desc: "Create a new obligation" },
      { method: "GET",  path: "/api/v1/obligations/{id}",  desc: "Fetch obligation details" },
      { method: "PATCH", path: "/api/v1/obligations/{id}", desc: "Mark complete / update due date" },
      { method: "DELETE", path: "/api/v1/obligations/{id}", desc: "Delete an obligation" },
    ],
  },
  {
    tag: "Critical Dates",
    color: "bg-amber-100 text-amber-800",
    dotColor: "bg-amber-500",
    endpoints: [
      { method: "GET",  path: "/api/v1/critical-dates",        desc: "List all critical dates" },
      { method: "POST", path: "/api/v1/critical-dates",        desc: "Create a critical date milestone" },
      { method: "GET",  path: "/api/v1/critical-dates/{id}",   desc: "Retrieve a critical date" },
      { method: "PATCH", path: "/api/v1/critical-dates/{id}",  desc: "Update date or notes" },
      { method: "DELETE", path: "/api/v1/critical-dates/{id}", desc: "Remove a critical date" },
    ],
  },
  {
    tag: "Analytics",
    color: "bg-cyan-100 text-cyan-800",
    dotColor: "bg-cyan-500",
    endpoints: [
      { method: "GET", path: "/api/v1/analytics/portfolio-risk",       desc: "Portfolio-wide clause risk summary" },
      { method: "GET", path: "/api/v1/analytics/expiring-leases",      desc: "Leases expiring within N days" },
      { method: "GET", path: "/api/v1/analytics/obligation-compliance", desc: "Obligation compliance rate" },
      { method: "GET", path: "/api/v1/analytics/lease-status",         desc: "Status distribution across portfolio" },
    ],
  },
];

const METHOD_STYLES: Record<string, string> = {
  GET:    "bg-sky-600 text-white",
  POST:   "bg-indigo-600 text-white",
  PATCH:  "bg-amber-500 text-white",
  DELETE: "bg-red-500 text-white",
  PUT:    "bg-teal-600 text-white",
};

export function ApiDocsPage() {
  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* ── Dark sidebar ──────────────────────────────────────── */}
      <aside className="w-64 bg-[#1e1b4b] text-white flex flex-col shrink-0">
        {/* Logo */}
        <div className="px-6 py-5 border-b border-indigo-800">
          <div className="flex items-center gap-2">
            <span className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center text-white font-bold text-sm">L</span>
            <div>
              <p className="text-sm font-bold text-white leading-tight">LeaseIQ AI</p>
              <p className="text-xs text-indigo-300">API Reference v1.0</p>
            </div>
          </div>
        </div>

        {/* Nav groups */}
        <nav className="flex-1 overflow-y-auto py-4 px-3">
          <p className="px-3 py-1 text-xs font-semibold text-indigo-400 uppercase tracking-widest mb-2">Resources</p>
          {ENDPOINT_GROUPS.map((group) => (
            <a
              key={group.tag}
              href={`#group-${group.tag.toLowerCase().replace(/\s+/g, "-")}`}
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-indigo-200 hover:bg-indigo-800 hover:text-white transition mb-0.5"
            >
              <span className={`w-2 h-2 rounded-full ${group.dotColor}`} />
              {group.tag}
              <span className="ml-auto text-xs text-indigo-400">{group.endpoints.length}</span>
            </a>
          ))}

          <div className="mt-6 border-t border-indigo-800 pt-4">
            <p className="px-3 py-1 text-xs font-semibold text-indigo-400 uppercase tracking-widest mb-2">Interactive</p>
            <a
              href={`${BASE_URL}/api/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-indigo-200 hover:bg-indigo-800 hover:text-white transition"
            >
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              Live Swagger UI
              <span className="ml-auto text-xs">↗</span>
            </a>
            <a
              href={`${BASE_URL}/api/redoc`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-indigo-200 hover:bg-indigo-800 hover:text-white transition"
            >
              <span className="w-2 h-2 rounded-full bg-sky-400" />
              ReDoc
              <span className="ml-auto text-xs">↗</span>
            </a>
          </div>
        </nav>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-indigo-800">
          <p className="text-xs text-indigo-400">Base URL</p>
          <p className="text-xs text-indigo-200 font-mono mt-0.5 break-all">{BASE_URL}/api/v1</p>
        </div>
      </aside>

      {/* ── Main content ──────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto">
        {/* Header */}
        <div className="bg-[#1e1b4b] text-white px-10 py-10">
          <div
            className="inline-block text-xs font-semibold text-indigo-300 bg-indigo-900 px-3 py-1 rounded-full mb-3"
          >
            REST API — v1.0.0
          </div>
          <h1 className="text-4xl font-bold tracking-tight">LeaseIQ AI API Reference</h1>
          <p className="mt-3 text-indigo-200 max-w-2xl">
            Full-stack commercial lease intelligence platform. Manage leases, extract clauses,
            track obligations, and surface AI-powered risk analytics.
          </p>
          <div className="mt-6 flex gap-3 flex-wrap">
            <span className="px-3 py-1 bg-indigo-700 rounded-lg text-sm text-indigo-100">
              JWT Bearer Auth
            </span>
            <span className="px-3 py-1 bg-indigo-700 rounded-lg text-sm text-indigo-100">
              JSON / REST
            </span>
            <span className="px-3 py-1 bg-indigo-700 rounded-lg text-sm text-indigo-100">
              Rate limited · 60 req/min
            </span>
          </div>
        </div>

        {/* Auth callout */}
        <div className="px-10 py-6 bg-indigo-50 border-b border-indigo-100">
          <h2 className="text-sm font-semibold text-indigo-900 mb-1">Authentication</h2>
          <p className="text-sm text-indigo-700">
            All protected endpoints require a{" "}
            <code className="bg-indigo-100 px-1.5 py-0.5 rounded font-mono text-xs">
              Authorization: Bearer &lt;token&gt;
            </code>{" "}
            header. Obtain a token via{" "}
            <code className="bg-indigo-100 px-1.5 py-0.5 rounded font-mono text-xs">
              POST /api/v1/auth/token
            </code>.
          </p>
        </div>

        {/* Endpoint groups */}
        <div className="px-10 py-8 space-y-10">
          {ENDPOINT_GROUPS.map((group) => (
            <section
              key={group.tag}
              id={`group-${group.tag.toLowerCase().replace(/\s+/g, "-")}`}
            >
              <div className="flex items-center gap-3 mb-4">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${group.color}`}>
                  {group.tag}
                </span>
                <span className="text-xs text-gray-400">{group.endpoints.length} endpoints</span>
              </div>

              <div className="space-y-2">
                {group.endpoints.map((ep, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-4 bg-white border border-gray-100 rounded-xl px-5 py-4 shadow-sm hover:shadow-md transition"
                  >
                    <span
                      className={`text-xs font-bold px-2.5 py-1 rounded-md w-16 text-center shrink-0 ${
                        METHOD_STYLES[ep.method] ?? "bg-gray-600 text-white"
                      }`}
                    >
                      {ep.method}
                    </span>
                    <code className="text-sm font-mono text-gray-700 flex-1">{ep.path}</code>
                    <span className="text-sm text-gray-500 hidden md:block">{ep.desc}</span>
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>

        {/* Live Swagger embed */}
        <div className="px-10 pb-10">
          <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
            <div className="bg-[#1e1b4b] px-6 py-3 flex items-center gap-3">
              <span className="w-3 h-3 rounded-full bg-red-400" />
              <span className="w-3 h-3 rounded-full bg-amber-400" />
              <span className="w-3 h-3 rounded-full bg-emerald-400" />
              <span className="ml-3 text-sm text-indigo-200 font-medium">
                Interactive Swagger UI — {BASE_URL}/api/docs
              </span>
            </div>
            <iframe
              src={`${BASE_URL}/api/docs`}
              title="LeaseIQ AI — Interactive API Docs"
              className="w-full"
              style={{ height: "720px", border: "none" }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
