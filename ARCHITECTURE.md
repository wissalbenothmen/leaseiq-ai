# Architecture — LeaseIQ AI

## System diagram

```
            ┌──────────────────────────────────────────────────────┐
            │                  React SPA  (:5022)                  │
            │  Vite · TS · Tailwind · TanStack Query · Recharts    │
            │  Lazy routes · ErrorBoundary · Design-system UI      │
            └──────────────────────────┬───────────────────────────┘
                                       │  HTTPS + JWT (Bearer)
                                       ▼
            ┌──────────────────────────────────────────────────────┐
            │            FastAPI async app  (:8022)                │
            │  Security headers · slowapi rate limit · request-ID  │
            │  Branded Swagger UI at /api/docs                     │
            └───┬───────────────────────┬──────────────────────────┘
                │                       │
        ┌───────▼────────┐      ┌───────▼────────┐
        │ SQLAlchemy 2   │      │ AI services    │
        │ async (asyncpg │      │ - clause scorer│
        │ / aiosqlite)   │      │ - abstractor   │
        └───────┬────────┘      └───────┬────────┘
                │                       │
                ▼                       ▼
        ┌───────────────┐      ┌────────────────────────┐
        │ Postgres /    │      │ OpenAI Chat Completions │
        │ SQLite (dev)  │      │ (JSON mode · retry · TO)│
        │ 8 tables      │      │ ↳ rule-based fallback   │
        └───────────────┘      └────────────────────────┘
```

## Modules

### Backend (`backend/app/`)

| Module | Purpose |
|---|---|
| `main.py` | App init, CORS, slowapi rate limit, security-headers middleware, request-ID tracing, branded Swagger UI, `/health` + `/ready` checks |
| `config.py` | `pydantic-settings`, SECRET_KEY strength validator with weak-key blocklist |
| `auth.py` | JWT HS256 encode/decode, bcrypt password hashing, `get_current_user` dependency |
| `database.py` | Async SQLAlchemy engine + session factory |
| `models/` | ORM models: `User`, `CommercialLease`, `LeaseClause`, `Obligation`, `CriticalDate`, `AuditLog`, `LeaseDocument`, `ClauseQuery` |
| `schemas/` | Pydantic request / response models |
| `routers/auth.py` | `register`, `login`, `me` |
| `routers/leases.py` | Lease CRUD + `/leases/{id}/detail` (aggregated view) + tenant briefing PDF |
| `routers/clauses.py` | Clause CRUD + AI `analyze` and `analyze-all` (persists `ai_summary`, `ai_recommendations`, `ai_analyzed_at`) |
| `routers/obligations.py` | Obligation CRUD, `overdue`, `upcoming`, `complete` |
| `routers/critical_dates.py` | Critical-date CRUD + portfolio `upcoming` view |
| `routers/analytics.py` | Portfolio risk summary, expiring leases, obligation compliance, status distribution |
| `services/clause_risk_scorer.py` | GPT clause scoring with JSON mode + retry-with-backoff. Falls back to a 300+ line deterministic rule engine when AI is unavailable. |
| `services/lease_abstractor.py` | GPT lease-term extraction with JSON mode + retry. Regex fallback. |
| `services/audit_service.py` | Append-only audit log writes |
| `services/tenant_briefing_pdf_service.py` | ReportLab-based PDF rendering |
| `services/whisper_service.py` | DeepInfra Whisper transcription (used by voice cross-validation endpoint) |
| `services/lease_clause_analyzer.py` | Voice ↔ clause cross-validation |

### Frontend (`frontend/src/`)

| Module | Purpose |
|---|---|
| `App.tsx` | Router with lazy-loaded routes, Suspense fallback, ErrorBoundary per protected route |
| `main.tsx` | QueryClient with `staleTime: 60s`, gcTime: 5min, `refetchOnWindowFocus: false` |
| `api/client.ts` | Axios client; reads JWT from `localStorage` on every request; 401 → redirect to `/login` once |
| `store/authStore.ts` | Zustand store: user + token |
| `pages/` | One file per route: Login, Dashboard, Leases, LeaseDetail, Obligations, Clauses, Analytics, ApiDocs |
| `components/ui/` | Design-system primitives: `Card`, `Badge`, `RiskBadge`, `StatusBadge`, `KpiCard`, `Button`, `EmptyState`, `AiSummary` |
| `components/ErrorBoundary.tsx` | Catches render errors per route |
| `components/Layout.tsx` | Top nav + page chrome |
| `types/` | TypeScript types mirroring backend responses |
| `utils/formatLabel.ts` | Currency, label, and clause-type formatters |

## Data flow

```
User action
   → React component (TanStack Query mutation)
   → Axios client (JWT header from localStorage)
   → FastAPI router (deps: get_current_user, get_db)
   → SQLAlchemy session + optional AI service
   → JSON response
   → Query invalidation → UI re-render
```

## Routes

| Prefix | Description |
|---|---|
| `/api/v1/auth` | `login`, `register`, `me` |
| `/api/v1/leases` | Lease CRUD + `/{id}/detail` + tenant briefing PDF + voice cross-validation |
| `/api/v1/clauses` | Clause CRUD + AI `analyze` + `analyze-all` |
| `/api/v1/obligations` | Obligation CRUD + `overdue` + `upcoming` + `complete` |
| `/api/v1/critical-dates` | Critical-date CRUD + portfolio `upcoming` |
| `/api/v1/analytics` | Portfolio aggregations |
| `/health` | Liveness — fast, no dependencies |
| `/ready` | Readiness — pings DB, reports AI key configuration |
| `/api/docs` | Branded Swagger UI (custom indigo theme) |

## Security posture

- Bcrypt password hashing
- JWT HS256, 8-hour default expiry (configurable). **No refresh token yet** — roadmap.
- Security headers middleware: HSTS, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy, Cache-Control
- slowapi rate limiting — default 120 req/min, configurable
- CORS allow-list driven by `ALLOWED_ORIGINS`
- SECRET_KEY strength validator: minimum 32 chars + weak-key blocklist
- Full audit-log table — populated by `audit_service.log_action()` from every mutating route

See [SECURITY.md](./SECURITY.md) for the full posture + responsible-disclosure policy.

## AI reliability

The clause risk scorer and lease abstractor both follow the same pattern:

1. Build prompt
2. Call OpenAI with `response_format={"type": "json_object"}` and a 30 second timeout
3. On transient error, retry up to 3 times with exponential backoff (0.5s → 1s → 2s)
4. On terminal failure, fall back to a deterministic rule engine that produces the same response shape
5. Log every call with model, token usage, and latency

This means **the product remains useful even if OpenAI is down or the key is missing** — the rule engine returns annotated results with the same response shape, just flagged as low confidence.
