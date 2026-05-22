# LeaseIQ AI Backend

FastAPI service for AI-driven commercial lease intelligence.

## Stack

FastAPI (async) · SQLAlchemy 2 (async) · Pydantic v2 · SQLite (dev) / PostgreSQL (prod) · OpenAI · bcrypt · JWT · slowapi

## Prerequisites

- Python 3.11+
- (Optional) Docker + PostgreSQL 14+ for production

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate              # Windows
# source .venv/bin/activate          # macOS / Linux
pip install -r requirements.txt
# .env is pre-populated for local dev — review and set OPENAI_API_KEY if you want live AI
python seed_data.py                   # creates SQLite db + 9 demo leases + 48 AI-scored clauses
uvicorn app.main:app --reload --port 8022
```

## Key environment variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing secret. Must be ≥ 32 chars and pass the weak-key validator in `config.py`. |
| `DATABASE_URL` | `sqlite+aiosqlite:///./leaseiq.db` (dev) or `postgresql+asyncpg://user:pass@host:5432/db` (prod) |
| `OPENAI_API_KEY` | Optional. Without it, services fall back to deterministic rule-based scoring. |
| `OPENAI_MODEL` | Default: `gpt-4.1-mini-2025-04-14` |
| `ALLOWED_ORIGINS` | JSON array of CORS origins |
| `RATE_LIMIT_PER_MINUTE` | Default 120 |
| `CLAUSE_RISK_HIGH_THRESHOLD` | Score ≥ this = HIGH (default 70.0) |
| `CRITICAL_DATE_ALERT_DAYS` | JSON int array — alert thresholds (default `[7,30,60,90]`) |

Full list in `app/config.py`.

## Testing

```bash
pytest -v
```

## API documentation

- Branded Swagger UI: http://localhost:8022/api/docs
- ReDoc: http://localhost:8022/api/redoc
- OpenAPI JSON: http://localhost:8022/openapi.json

## Health checks

- `GET /health` — liveness, no dependencies
- `GET /ready` — readiness, pings the database and reports whether the AI key is configured
