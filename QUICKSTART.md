# Quick Start — LeaseIQ AI

5 minutes from clone to running app, including seeded demo data.

## Prerequisites

Python 3.11+, Node.js 18+, Git.

## Steps

```bash
git clone <repo-url> && cd project_22_leaseiq_ai

# 1. Backend
cd backend
python -m venv .venv && .venv\Scripts\activate    # Windows
# source .venv/bin/activate                         # macOS / Linux
pip install -r requirements.txt
python seed_data.py                                 # creates SQLite db with 9 leases + AI commentary
uvicorn app.main:app --reload --port 8022

# 2. Frontend  (new terminal)
cd frontend
npm install
npm run dev                                          # http://localhost:5022
```

Open http://localhost:5022 and log in:

| Role | Email | Password |
|---|---|---|
| Portfolio manager | `admin@leaseiq.demo` | `Admin123!` |
| Analyst | `analyst@leaseiq.demo` | `Analyst123!` |
| Viewer | `viewer@leaseiq.demo` | `Viewer123!` |

## What's already loaded

- 9 commercial leases (offices, retail, industrial, biotech, aviation, data centre)
- 48 risk-scored clauses with AI summary + recommendations
- 36 obligations across overdue, upcoming, and completed states
- 28 critical dates (expirations, renewal-option notices, escalations, environmental reviews)

## Optional — live AI

Without an OpenAI key, the rule-based scorer powers the Re-analyze button. To enable live GPT analysis:

```bash
# backend/.env
OPENAI_API_KEY=sk-...
```

Both `lease_abstractor` and `clause_risk_scorer` will use GPT with JSON-mode, retry-with-backoff, and 30s timeouts.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Backend won't start: `SECRET_KEY is too weak` | The `.env` ships with a strong key; if you regenerated it, ensure length ≥ 32 chars |
| Blank page on http://localhost:5022 | Make sure backend is running on `:8022` and `VITE_API_URL` matches |
| `python seed_data.py` fails with bcrypt warning | Cosmetic — passlib + bcrypt 4.x. Seed still completes. |
| Want a clean slate | Delete `backend/leaseiq.db` and re-run `python seed_data.py` |
