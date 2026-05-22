# Changelog

## [1.1.0] — 2026-05-21

### Added

- Persistent AI analysis on clauses: `ai_summary`, `ai_recommendations`, `ai_analyzed_at` columns
- `<AiSummary>` component rendering AI commentary on Clauses + Lease Detail pages
- Dashboard "AI Briefing" card with derived insights from live portfolio data
- Frontend design system: `Card`, `Badge`, `RiskBadge`, `StatusBadge`, `KpiCard`, `Button`, `EmptyState`, `AiSummary`, `ErrorBoundary`
- Lazy-loaded routes with `Suspense` fallback
- Backend `/ready` endpoint — pings DB and reports AI configuration
- OpenAI calls: JSON mode + retry-with-exponential-backoff + 30s timeout + token-usage logging
- `seed_data.py` — 9 commercial leases, 48 AI-scored clauses, 36 obligations, 28 critical dates

### Changed

- `apiClient` reads token from `localStorage` on every request (single source of truth)
- `QueryClient` defaults: `staleTime: 60s`, `gcTime: 5min`, `refetchOnWindowFocus: false`
- Leases page: portfolio KPIs (size, monthly rent, expiring), per-row days-remaining indicator
- Obligations page: confirm-to-complete modal, total-amount KPI, design-system primitives
- Documentation rewritten to match actual code; removed claims about un-implemented Celery, Azure DI, upload page

### Removed

- Duplicate / debug screenshots and `*.console.json` debug artifacts from `project-audit/screenshots/`

## [1.0.0] — 2026-05-17

### Added

- Initial release
- AI clause extraction and risk scoring
- Lease management with tenant + landlord records
- Obligation registry + escalation
- Critical-date tracking + alert flags
- Branded Swagger UI at `/api/docs`
- React dashboard with portfolio analytics
- JWT authentication (portfolio manager / analyst / viewer roles)
- Demo seed data

### Security

- bcrypt password hashing, JWT auth, CORS restriction, rate limiting, security-headers middleware
