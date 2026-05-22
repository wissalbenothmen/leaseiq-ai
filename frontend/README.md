# LeaseIQ AI Frontend

React 18 + TypeScript + Vite SPA. Lazy-loaded routes, design-system primitives, TanStack Query for server state, Zustand for auth.

## Prerequisites

- Node.js 18+
- npm 9+

## Setup

```bash
cd frontend
npm install
npm run dev          # http://localhost:5022
```

The dev server proxies to the backend at `VITE_API_URL` (defaults to `http://localhost:8022/api/v1`).

## Scripts

```bash
npm run dev          # Vite dev server with HMR
npm run build        # production build → dist/
npm run preview      # preview the production build
npm run type-check   # tsc --noEmit
npm run lint         # eslint
```

## Environment

Create `.env.local` (optional):

```
VITE_API_URL=http://localhost:8022/api/v1
```

## Design system

`src/components/ui/` houses the design-system primitives. **Use these instead of hand-rolling Tailwind classes.**

| Component | Purpose |
|---|---|
| `<Card>` | Surface container with `Card.Header` / `Card.Body` slots |
| `<Button variant size>` | Primary, secondary, ghost, danger |
| `<Badge variant size>` | Neutral, success, warning, danger, info, brand |
| `<RiskBadge score>` | Risk-score-coloured badge — HIGH ≥ 70, MED 40–69, LOW < 40 |
| `<StatusBadge status>` | Lease + obligation status badge |
| `<KpiCard variant>` | KPI tile: neutral, critical, warning, info, success |
| `<EmptyState>` | Icon + title + description + action |
| `<AiSummary>` | AI commentary block with summary + recommendations + factors + analyzed timestamp |
| `<AiBadge>` | Inline ✦ AI chip |

## Pages

| Route | Description |
|---|---|
| `/login` | Login (glassmorphism card, animated gradient blobs) |
| `/dashboard` | KPIs + AI briefing + risk + expiry charts |
| `/leases` | Searchable, filterable lease portfolio with risk & rent KPIs |
| `/leases/:id` | Lease detail: overview, clauses (with AI commentary), obligations, dates |
| `/clauses` | Cross-portfolio clause analysis, risk-tier filters |
| `/obligations` | Overdue + upcoming filter, confirm-to-complete modal |
| `/analytics` | Recharts portfolio analytics |
| `/docs` | Branded Swagger UI |

## Performance

- Each route is `React.lazy()`-imported with `<Suspense>` fallback — first paint is small.
- Errors are caught by `ErrorBoundary` and rendered with a recover button.
- `QueryClient` defaults: `staleTime: 60s`, `gcTime: 5min`, `refetchOnWindowFocus: false`.
